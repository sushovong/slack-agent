#!/bin/bash

if [[ $# -ne 1 ]]; then
    echo "USAGE: ./setup.sh <project-id>"
    echo "<project-id>: will be used for the service-name"
    exit 1
fi

EMAIL_REGEX='.+@udaan\.com$'
if [[ -n "${CODEOWNERS}" && "$CODEOWNERS" =~ $EMAIL_REGEX ]]; then
    echo "* $CODEOWNERS" > CODEOWNERS
else
    if git config user.email | grep -E "$EMAIL_REGEX" >/dev/null; then
        echo "* $(git config user.email)" > CODEOWNERS
    else
        echo "Please configure git user.email to your @udaan.com email address."
        echo ""
        echo "(either) git config --global user.email <your-udaan-email>"
        echo "(or)     export CODEOWNERS=<your-udaan-email> # temporary for this script"
        echo ""
        echo "Then run this script again."
        exit 1
    fi
fi

export LC_CTYPE=C
export LANG=C

PROJECT_ID="$1"

find .github/workflows/ -type f -exec sed -i '' -e '/XX\/tpl/d' {} \;
sed -i '' -e "s@project: blank-project-docker@project: $PROJECT_ID@" server-config.yaml;

echo "${PROJECT_ID}" > README.md
echo "===" >> README.md

git rm ./setup.sh
