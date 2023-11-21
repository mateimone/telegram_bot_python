# telegram_bot

Welcome to 'telegram_bot_python'!\
This is my first personal project, and the first time I've worked with the
Telegram and GitHub API. The only external resource you'll need is Ngrok, an application that makes your local
address visible on the internet. After you've installed Ngrok, you'll only need to open it and follow the instructions
to be able to receive notifications on your project, or to even add resources to it.

Firstly, clone the project and install the dependencies. Then, open up a command line and run the command
```python /path/to/src/main.py```
This command accepts one additional parameter, debug. Write 'True' if you want any notification to be saved to a file,
as you can see more information there, although in JSON format as sent by GitHub. Writing anything else or leaving it
empty will assign False to that parameter.
**Note**: run this from a command line; otherwise, the bot might encounter problems when reading and writing to the user data file.

Now, you will want to set Ngrok as a $PATH$ variable. If you don't know how to do this, follow this [guide](https://www.educative.io/answers/how-to-add-an-application-path-to-system-environment-variables).
After you've done this, open up Ngrok and run the command
```ngrok http http://127.0.0.1:4040```
It is essential that you first run the python script, and then the Ngrok command. Otherwise, the program might not work.

Finally, let's put them all together. To receive notifications, you need to add webhooks to GitHub that connect
to the address Ngrok is exposing. For GitHub to let you add webhooks, you will need to provide a sort of identification.
This can be done by running a few commands on Telegram.
Open it up, search for '@matei_github_bot', and press on start. Now, you will need to run the following:
```
/linkghrepo param - links the bot to the repository name given as param
/linkghtoken param - links the bot to the GitHub token given as param
/linkghusername param - links the bot to the username given as param
```
The GitHub repo is the name of the repository you want to add the webhooks to.\
The GitHub token is your personal token that will be used to access the GitHub API (found [here](https://github.com/settings/tokens)).\
The GitHub username is, well, the username you have on GitHub.

The repo, token, and username can still be used to create issues, branch, and other resources.
Finally, look at the Ngrok terminal and take the port of the **web interface** address.
Run one last command, with param = web interface port
```
/auto_set_webhooks param - automatically sets webhooks for updates on ngrok's web interface port
```
**Note**: webhooks can only be set by a repository owner or by someone who has admin access.\
After a few seconds, you should receive a message on Telegram stating that the webhooks are set. You will now receive
notifications for certain updates on GitHub. A list of notifications can be found below.

If you want to close the program, simply exit both Ngrok and python terminals. The bot will retain the information that
you provided through the 3 'link commands'. The webhook command will have to be run again, since the address Ngrok
is creating for you changes each time you restart the process. Just follow the instructions above for it. If there were
previously generated webhooks, they will be deleted and replaced by new ones with the correct new address.
**Note**: if you want to make sure the webhooks will be deleted correctly, you might not want to modify the generated ones;
if you add your own webhooks or modify the existing ones, they will probably not be deleted (unless you make a webhook
with only one of the events that is automatically generated).

List of notifications:
```
Branch or tag created (create)
Branch or tag deleted (delete)
Issue opened, edited, deleted, transferred, pinned, unpinned, closed, reopened, assigned, unassigned, labeled, unlabeled, milestoned, demilestoned, locked, or unlocked. (Issues)
Issue comment (issue_comment)
Commit comment (commit_comment)
Milestone created, edited or deleted (milestone)
Label created, edited or deleted (label)
Push events (push)
Pull requests (pull_request)
Pull request review (pull_request_review)
Pull request review comment (pull_request_review_comment)
Team add (team_add)
```

List of resources you can add:
```
Issue creation (with title and body)
Branch creation (with title and optional source branch) - if source branch is not given, it will be considered main; if main is renamed, the branch won't be found
```
