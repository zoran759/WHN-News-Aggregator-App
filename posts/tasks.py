from __future__ import absolute_import, unicode_literals
from celery import shared_task
import requests
import json
from urllib.parse import urlparse
from django.core.files import File
from django.utils.timezone import datetime
import logging

HUBSPOT_API_KEY = '6384ea2f-48d2-4672-a92a-2d4b30a9be26'

@shared_task
def create_or_update_contact_hubspot(user_id, activation_key=None):
	from django.contrib.auth import get_user_model
	user = get_user_model().objects.get(id=user_id)
	endpoint = 'https://api.hubapi.com/contacts/v1/contact/createOrUpdate/email/' + user.email \
	           + '/?hapikey=' + HUBSPOT_API_KEY
	headers = {
		"Content-Type": "application/json"
	}
	properties = {
		"properties": [
			{
				"property": "username",
				"value": user.username
			},
			{
				"property": "email_confirmed",
				"value": user.is_active
			}
		]
	}
	if activation_key:
		properties['properties'].append({
			"property": "conformation_url",
			"value": "https://news.viceroy.tech/accounts/activate/" + str(activation_key) + "/"
		})
	if user.first_name:
		properties['properties'].append({
			"property": "firstname",
			"value": user.first_name
		})
	if user.last_name:
		properties['properties'].append({
			"property": "lastname",
			"value": user.last_name
		})
	data = json.dumps(properties)

	r = requests.post(url=endpoint, data=data, headers=headers)

	if r.status_code == 400:
		response = json.loads(r.content)
		error = response['validationResults'][0]['error']
		if error == "PROPERTY_DOESNT_EXIST" and response['validationResults'][0]['name'] == 'email_confirmed':
			options = [
				{
					"label": "Yes",
					"value": True
				},
				{
					"label": "No",
					"value": False
				}
			]
			create_new_property_hubspot(response['validationResults'][0]['name'], 'booleancheckbox', options=options)
			create_or_update_contact_hubspot(user_id, activation_key)
		elif error == "PROPERTY_DOESNT_EXIST" and response['validationResults'][0]['name'] == 'username':
			create_new_property_hubspot(response['validationResults'][0]['name'], 'text')
			create_or_update_contact_hubspot(user_id, activation_key)
	elif r.status_code != 200:
		raise BaseException(json.loads(r.content))
	user.userprofile.hubspot_contact = True
	user.userprofile.save()
	return r


@shared_task
def create_new_property_hubspot(field_name, field_type, options=None):
	"""
	Creates new property on HubSpot
	:param field_name: The name for the new property must be a string
	:param field_type: The type for the new property must be one of these:
	textarea - a <textarea> field, stores data as a string
	text - a simple text box, stores a string
	date - a datepicker field, stores a date type
	file - stores the URL location of a file. Note: The file itself must be stored separately,
	as the contact property cannot store the file, just the URL location of a file. Treated as a string.
	number - a number input field, stores a number value
	select - a dropdown box, uses the enumeration type
	radio - a set of radio buttons, used with the enumeration data type.
	checkbox - a set of checkboxes, used with the enumeration data type
	booleancheckbox - a single checkbox, stores "true" (as a string) if checked.
	:param options: Example:
	options = [
				{
					"label": "Yes",
					"value": True
				},
				{
					"label": "No",
					"value": False
				}
			]
	:return: response of a request
	"""
	if field_type not in ['textarea', 'text', 'date', 'file', 'number',
	                      'select', 'radio', 'checkbox', 'booleancheckbox']:
		raise ValueError('Must be one of these types: textarea, text, date, file, number, '
		                 'select, radio, checkbox, booleancheckbox.')

	if not isinstance(field_name, str):
		raise TypeError('Must be a string.')

	if options is None:
		options = []

	endpoint = 'https://api.hubapi.com/properties/v1/contacts/properties?hapikey=' + HUBSPOT_API_KEY
	headers = {
		"Content-Type": "application/json"
	}
	name = field_name
	name_formatted = name.replace('_', ' ').capitalize()

	data = json.dumps(
		{
			"name": name,
			"label": name_formatted,
			"description": "Auto property - %s" % name_formatted,
			"groupName": "contactinformation",
			"type": 'string',
			"fieldType": field_type,
			"formField": False,
			"options": options
		}
	)

	r = requests.post(url=endpoint, data=data, headers=headers)

	return json.loads(r.content)


@shared_task
def update_contact_property_hubspot(email, property_name, value, options=None):
	"""
	Updating or creating property on Hubspot.
	"""
	if not isinstance(email, str) and not isinstance(property_name, str):
		raise TypeError('Must be a string.')

	endpoint = 'https://api.hubapi.com/contacts/v1/contact/email/' + email + '/profile?hapikey=' + HUBSPOT_API_KEY
	headers = {
		"Content-Type": "application/json"
	}
	data = json.dumps({
		"properties": [
			{
				"property": property_name,
				"value": value
			}
		]
	})

	r = requests.post(endpoint, data=data, headers=headers)

	if r.status_code == 400:
		field_type = 'text'
		if isinstance(value, str):
			field_type = 'text'
		elif isinstance(value, bool):
			field_type = 'booleancheckbox'
		elif isinstance(value, int):
			field_type = 'number'

		create_new_property_hubspot(property_name, field_type=field_type, options=options)
		r = requests.post(endpoint, data=data, headers=headers)

	return r.status_code


@shared_task
def update_access_token_feedly():
	from posts.models import FeedlyAPISettings
	feedly_settings = FeedlyAPISettings.get_solo()
	feedly = feedly_settings.get_client()
	response = feedly.refresh_access_token(feedly_settings.FEEDLY_API_REFRESH_TOKEN)
	feedly_settings.FEEDLY_API_ACCESS_TOKEN = response.get('access_token')
	feedly_settings.save()


@shared_task
def get_feedly_articles():
	from posts.models import FeedlyAPISettings, Post, NewsAggregator
	from django.contrib.auth import get_user_model
	from posts.utils import get_favicon
	feedly_settings = FeedlyAPISettings.get_solo()
	tag_on_feedly = 'WHN'
	feedly = feedly_settings.get_client()
	data = feedly.get_enterprise_user_tags(feedly_settings.FEEDLY_API_ACCESS_TOKEN)
	whn_tag_id = False
	for i in data:
		label = i.get('label', False)
		if label and label == tag_on_feedly:
			whn_tag_id = i.get('id', False)
			break
	if whn_tag_id:
		articles = feedly.get_feed_content(
			feedly_settings.FEEDLY_API_ACCESS_TOKEN,
			whn_tag_id
		)
		if articles.get('items', False):
			admin = get_user_model().objects.filter(is_superuser=True)[0]
			last_entry_id = ''
			for article in articles['items']:
				try:
					post = Post.objects.get(title=article.get('title', ''))
				except Post.DoesNotExist:
					origin_url = urlparse(article.get('origin').get('htmlUrl'))
					if 'google' in origin_url.netloc:
						article['origin']['htmlUrl'] = article.get('alternate')[0]['href'] if article.get('alternate', None) else article.get('canonicalUrl')
						article['origin']['title'] = urlparse(article['origin']['htmlUrl']).netloc
					try:
						news_aggregator = NewsAggregator.objects.get(name=article.get('origin').get('title'))
					except NewsAggregator.DoesNotExist:
						na_url = urlparse(article['origin']['htmlUrl'])
						news_aggregator = NewsAggregator.objects.create(name=article.get('origin').get('title'),
						                                                url=na_url.scheme + '://' + na_url.netloc)

						temp_image = get_favicon(article.get('origin').get('htmlUrl'))
						if temp_image:
							try:
								news_aggregator.logo.save(na_url.netloc + "_logo", File(temp_image))
							except OSError:
								logging.warning("Can't save logo image for news_aggregator: "
								                + str(news_aggregator.id) + '--' + str(news_aggregator.name))
							news_aggregator.save()

					if article.get('title', False) and news_aggregator and article.get('unread', False):
						post = Post.objects.create(submitter=admin, title=article.get('title'),
						                           news_aggregator=news_aggregator,
						                           submit_time=datetime.fromtimestamp(article.get('published')/1000.0),
						                           url=article['canonicalUrl'] if article.get('canonicalUrl', None) else article.get('alternate')[0]['href'],
						                           feedly_engagement=article.get('engagement', 100))
					else:
						raise Exception("Article doesn't have title.")

				article_image = article.get('visual', False)
				if article_image:
					post.image_url = article_image.get('url', None)
					post.save()
				last_entry_id = article.get('id')

			feedly.mark_tag_read(feedly_settings.FEEDLY_API_ACCESS_TOKEN, whn_tag_id, last_entry_id)

		else:
			raise Exception("No entries are found with '%s' tag." % tag_on_feedly)
	else:
		raise Exception("Can't find '%s' tag!" % tag_on_feedly)


@shared_task
def get_feedly_article(request_content):
	from posts.models import FeedlyAPISettings, Post, NewsAggregator
	from django.contrib.auth import get_user_model
	from posts.utils import get_favicon
	feedly_settings = FeedlyAPISettings.get_solo()
	feedly = feedly_settings.get_client()
	article = feedly.get_entry(feedly_settings.FEEDLY_API_ACCESS_TOKEN, request_content.get('entryId'))[0]
	try:
		Post.objects.get(title=request_content.get('title', None))
	except Post.DoesNotExist:
		origin_url = urlparse(article.get('origin').get('htmlUrl'))
		if 'google' in origin_url.netloc:
			article['origin']['htmlUrl'] = article.get('alternate')[0]['href'] if article.get('alternate',
			                                                                                  None) else article.get(
				'canonicalUrl')
			article['origin']['title'] = urlparse(article['origin']['htmlUrl']).netloc
		try:
			news_aggregator = NewsAggregator.objects.get(name=article.get('origin').get('title'))
		except NewsAggregator.DoesNotExist:
			na_url = urlparse(article['origin']['htmlUrl'])
			news_aggregator = NewsAggregator.objects.create(name=article.get('origin').get('title'),
			                                                url=na_url.scheme + '://' + na_url.netloc)
			temp_image = get_favicon(na_url.geturl())
			if temp_image:
				news_aggregator.logo.save(
					origin_url.netloc + "_logo",
					File(temp_image,
					     name=origin_url.netloc + "_logo"))
				news_aggregator.save()

		if request_content.get('title', False) and news_aggregator:
			post = Post.objects.create(submitter=get_user_model().objects.filter(is_superuser=True)[0],
			                           author=request_content.get('author', None),
			                           title=request_content.get('title'),
			                           news_aggregator=news_aggregator,
			                           submit_time=datetime.fromtimestamp(
				                           request_content.get('publishedTimestamp') / 1000.0),
			                           url=article['canonicalUrl'] if article.get('canonicalUrl', None) else article.get('alternate')[0]['href'],
			                           feedly_engagement=article.get('engagement', 100))

			article_image = request_content.get('visualUrl', None)
			if article_image:
				post.image_url = article_image
				post.save()
