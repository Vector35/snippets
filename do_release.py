#!/usr/bin/env python3
#Little utility to automatically do a new release.
from git import Repo
from json import load, dump
from github_release import gh_release_create
from sys import exit
from argparse import ArgumentParser
from subprocess import run

parser = ArgumentParser()
parser.add_argument("-d", "--description", help="Description for the new release", action="store", dest="description", default="")
parser.parse_args()

repo = Repo(".")
reponame = list(repo.remotes.origin.urls)[0].split(':')[1].split('.')[0]

with open('plugin.json') as plugin:
	data = load(plugin)

for tag in repo.tags:
	if tag.name == data['version']:
		print(f"Current plugin version {data['version']} is already a tag. Shall I increment it for you?")
		yn = input("[y/n]: ")
		if yn == "Y" or yn == "y":
			digits = data['version'].split('.')
			newlast = str(int(digits[-1])+1)
			digits[-1] = newlast
			new_version = '.'.join(digits)
			data['version'] = new_version
			print(f"Updating plugin with new version {new_version}")
			run("./generate_plugininfo.py -r -f", check=True)
			with open('plugin.json') as plugin:
				dump(data, plugin)
			repo.git.add('plugin.json')
			repo.git.add('README.md')
			repo.git.commit(f"Updating to {new_version}")
			repo.git.push('origin')
		else:
			print("Stopping...")
			exit(-1)

# Create new tag
new_tag = repo.create_tag(data['version'])
# Push
repo.remotes.origin.push(data['version'])
# Create release
gh_release_create(reponame, data['version'], publish=True, name="%s v%s" % (data['name'], data['version']))
