#!/bin/bash

[ -z "$USER" ] && read -ep "USERNAME: " USER
[ -z "$PASS" ] && read -ep "PASS (oauth:xxxxxx): " PASS

( echo "PASS $PASS" ; echo "NICK $USER" ; cat ) \
    | openssl s_client -connect irc.chat.twitch.tv:6697
