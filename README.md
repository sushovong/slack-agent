blank-project-docker
====================

# overview

This project is a GitHub template to make it easy to create new docker projects. It sets up the following:

- a blank Dockerfile
- a baseline server-config.yaml
- GHA workflow files

# usage

To use this repo, click on the green "Use this template" button at
[https://github.com/udaan-com/udaan-blank-project-docker](https://github.com/udaan-com/udaan-blank-project-docker)
and give your project a name.

Let's say your project is called "udaan-hello-docker". Do the following next:

Clone your repo:

```
git clone git@github.com:udaan-com/udaan-hello-docker.git
```

Run setup.sh:

```
USAGE: ./setup.sh <project-id>
<project-id>: will be used for the service-name
```

```
./setup.sh hello-docker
```

Commit the changes:

```bash
git add .
git commit --amend -a -m'Initial commit; basic project structure'
```

Push your changes:

```bash
git push -f
```

(Don't use the `-f` flag for `git push` in the future — this makes sense only
while initially setting up the project.)
