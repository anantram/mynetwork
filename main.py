#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import os
import jinja2

from google.appengine.ext import db
template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)


# 
# Database Tables
#

# Table to store user details
# User_name to store userID, f_name, l_name first and last name respectively
# u_pass password

class users_db(db.Model):
	user_name = db.StringProperty(required = True) 
	f_name = db.StringProperty(required = True)
	l_name = db.StringProperty()
	u_pass = db.StringProperty()

class friends_db(db.Model):
	user_name = db.StringProperty(required = True)
	user_friend = db.StringProperty()
	friend_name = db.StringProperty()

class posts_db(db.Model):
	user_name = db.StringProperty(required = True)
	user_post = db.StringProperty()

class comments_db(db.Model):
	post = db.StringProperty(required = True)
	post_comment = db.StringProperty()
	post_user = db.StringProperty()

class requests_db(db.Model):
	user_name = db.StringProperty(required = True)
	user_request = db.StringProperty()
	request_name = db.StringProperty()
# Functions starts

# Main class
class MainHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
    	self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
    	t = jinja_env.get_template(template)
    	return t.render(params)

    def render(self, template, **kw):
    	self.write(self.render_str(template, **kw))

    def get(self):
        self.render("home.html")

# Register Page
class register(MainHandler):
	def get(self):
		self.render("index.html",error ="")

	def post(self):
		passcheck = self.request.get("u_pass")
		passcheck1 = self.request.get("u_pass_check")
		user = self.request.get("u_email")
		fname = self.request.get("f_name")
		lname = self.request.get("l_name")
		if passcheck == passcheck1:
			userslist = db.GqlQuery("select * from users_db")
			users = userslist.fetch(100)
			doesexists = True
			for names in users:
				if names.user_name == user:
					self.render("index.html", error = "User already exists")
					doesexists = False
					break
			if doesexists:
				dbIn = users_db(user_name = user, f_name = fname, l_name = lname, u_pass = passcheck)
				dbIn.put()
				self.redirect("/login")
		else:
			self.render("index.html", error = "Password mismatch")

# Login page
class login(MainHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		self.render("signin.html", error = "")

	def post(self):
		user_name = self.request.get("uname")
		user_pass = self.request.get("upass")

		# Verifying the user
		abcd = db.GqlQuery("select * from users_db where user_name = '%(kwarg)s'" % {'kwarg':user_name})
		temp = abcd.get()
		if temp:
			if temp.u_pass == user_pass:
				temp_str = str(temp.f_name)
				temp2_str = str(temp.user_name)
				self.response.headers.add_header('Set-Cookie', 'log_user = %s' % temp_str)
				self.response.headers.add_header('Set-Cookie', 'log_username = %s' % temp2_str)
				self.redirect("/dashboard")
			else:
				self.render("signin.html", error = "Password mismatched")
		else:
			self.render("signin.html", error = "User doesnot exit")

# Main Dashboard
class home(MainHandler):
	def get(self):
		username = self.request.cookies.get('log_user')
		userID = self.request.cookies.get('log_username')
		if userID == "":
			self.redirect("/login")
		else:
			user_posts = db.GqlQuery("select * from posts_db where user_name = '%(kwarg)s'" % {'kwarg':userID})
			posts_out = user_posts.fetch(100)

			user_friend = db.GqlQuery("select * from friends_db where user_name = '%(kwarg)s'" % {'kwarg':userID})
			friends_out = user_friend.fetch(100)

			users = db.GqlQuery("select * from users_db where user_name != '%(kwarg)s'" % {'kwarg':userID})
			users_out = users.fetch(100)

			requests = db.GqlQuery("select * from requests_db where user_request = '%(kwarg)s'" % {'kwarg':userID})
			requests_out = requests.fetch(100)

			self.render("dash.html", username = username, userID = userID, posts = posts_out, users = users_out, user_friends = friends_out, requests = requests_out)
	
	def post(self):
		newpost = self.request.get("new_post")
		user_name = self.request.cookies.get('log_username')
		if user_name == "":
			self.redirect("/login")
		else:
			new_post= posts_db(user_name = user_name, user_post = newpost)
			new_post.put()
			self.redirect("/dashboard")

class logout(MainHandler):
	def get(self):
		self.response.headers.add_header('Set-Cookie', 'log_user = ""')
		self.response.headers.add_header('Set-Cookie', 'log_username = ""')
		self.redirect("/login")

class profile(MainHandler):
	def get(self):
		username = self.request.get("username")
		userID = self.request.get("userID")
		posts = db.GqlQuery("select * from posts_db where user_name = '%(kwarg)s'" % {'kwarg':userID})
		post_out = posts.fetch(100)
		isFriend = False
		request_send = False

		current_user = self.request.cookies.get('log_username')
		friend_list = db.GqlQuery("select * from friends_db where user_name = '%(kwarg)s'" % {'kwarg':current_user})
		friends = friend_list.fetch(100)
		for friend in friends:
			if friend.user_friend == userID:
				isFriend = True
				break

		if not isFriend:
			friend_requests = db.GqlQuery("select * from requests_db where user_name = '%(kwarg)s'" % {'kwarg':current_user})
			friends = friend_requests.fetch(100)
			for friend in friends:
				if friend.user_request == userID:
					request_send = True
					break

		self.render("profile.html", posts = post_out, username = username, friend_stat = isFriend, userID = userID, request_stat = request_send)

class post(MainHandler):
	def get(self):
		post = self.request.get("post")
		comments = db.GqlQuery("select * from comments_db where post = '%(kwarg)s'" % {'kwarg':post})
		comments_list = comments.fetch(100)
		self.render("post.html", post = post, comments_list = comments_list)
	def post(self):
		post = self.request.get("post")
		comment = self.request.get("comment")
		user = self.request.cookies.get('log_user')
		new_post = comments_db(post = post, post_comment = comment, post_user = user)
		new_post.put()
		self.redirect("/dashboard")

class addfriend (MainHandler):
	def get(self):
		username = self.request.cookies.get('log_username')
		friendname = self.request.get("friendname")
		friendID = self.request.get("friendID")
		user_name = self.request.cookies.get('log_user')
		dbIn = friends_db(user_name = friendID, user_friend = username, friend_name = user_name)
		dbIn.put()
		dbIn = friends_db(user_name = username, user_friend = friendID, friend_name = friendname)
		dbIn.put()
		delrequests = requests_db.all()
		for delrequest in delrequests:
			if delrequest.user_name == friendID:
				if delrequest.user_request == username:
					delrequest.delete()
		self.redirect("/dashboard")

class sendrequest (MainHandler):
	def get(self):
		username = self.request.cookies.get('log_username')
		user_name = self.request.cookies.get('log_user')
		friendname = self.request.get("friendname")
		friendID = self.request.get("friendID")
		dbIn = requests_db(user_name = username, user_request = friendID, request_name = user_name)
		dbIn.put()
		self.redirect("/dashboard")


class unfriend(MainHandler):
	def get(self):
		current_user = self.request.cookies.get('log_username')
		user_friend = self.request.get("friendID")
		friends = friends_db.all()
		for delfriend in friends:
			if delfriend.user_name == current_user :
				if delfriend.user_friend == user_friend :
					delfriend.delete()

		friends = friends_db.all()
		for delfriend in friends:
			if delfriend.user_name == user_friend :
				if delfriend.user_friend == current_user :
					delfriend.delete()
		self.redirect("/dashboard")

class delete(MainHandler):
	def get(self):
		delusers = posts_db.all()
		for deluser in delusers:
			deluser.delete()
		delusers = users_db.all()
		for deluser in delusers:
			deluser.delete()
		delusers = friends_db.all()
		for deluser in delusers:
			deluser.delete()
		delusers = comments_db.all()
		for deluser in delusers:
			deluser.delete()
		self.redirect("/signup")


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/login', login),
    ('/signup', register),
    ('/dashboard', home),
    ('/logout', logout),
    ('/profile', profile),
    ('/post', post),
    ('/addfriend', addfriend),
    ('/unfriend', unfriend),
    ('/sendrequest', sendrequest)
], debug=True)
