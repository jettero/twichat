
# WTF, another IRC client?

Yeah, well, writing Twitch bots is irritating using some of the already existing
IRC client APIs. I just wanted something really simple without any barriers or
assumptions about what a server does (or doesn't do) when you connect.

This stuff doesn't have to be all that complicated. In a sense IRC is just
sending and receiving lines of text. Their format just happens to follow RFC
1459 (among others).

Twitch intentionally limits the IRC functionality on its IRC based chat API.
So, here we have an async lib for sending and receiving lines and matching
patterns and formatting those patterns into objects via a proper parser.

Perhaps more importantly in the Twitch sense, if this API doesn't understand a
line, it will simply ignore it. And it imposes nearly zero expectations about
what replies should come after connect or send.

# Get a token

https://twitchapps.com/tmi/
