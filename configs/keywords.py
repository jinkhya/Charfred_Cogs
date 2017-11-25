#!/usr/bin/env python
# Keywords for Charfred to listen for, and those he should use himself!
# You don't need to list any command names or server names here,
# those are taken from the corresponding entries in the configs file.
# These lists are only for keywords/phrases which signify a valid command
# or are replies that Charfred will choose from.

# Keyphrases signify a valid command, they always stand at the end
# of the command.
keyphrases = ["won't you?",
              "will you?",
              "mustn't we?",
              "won't we?",
              "DO IT NOW!"]

# Command Acknowledgements; Charfred will use one of these to show that he
# has recieved and understood a command.
acks = ["Of course!",
        "Right away!",
        "Yes.",
        "No problemo!",
        "Promptly!",
        "With pleasure!",
        "With pleasure, as always!",
        "Thanks for the tip...",
        "*nods*"]

# Command Nacknowledgements; Charfred will use one of these to show that he
# has recieved, but not understood a command.
nacks = ["That doesn't look like anything to me.",
         "Doesn't look like anything to me.",
         "TAKE IT BACK!",
         "Rubber baby buggy bumpers!",
         "Don't you know the building is on fire?!",
         "*These violent delights have violent ends*",
         "I don't understand..."]

# Command Error; Charfred will let you know with one of these, that
# the command entered cannot be executed because of some error or
# insufficient permissions.
errormsgs = ["Sorry, you're not allowed to use that!",
             "I cannot let you do this!",
             "Stop screwing around!",
             "Uplinks underground, uplinks underground.\n"
             "If you guys don't shut up, I'll uplink your ass,\n"
             "and you'll be underground!",
             "STAHP IT!"]

# Reply Prefixes; Charfred will use one of these as a prefix for
# responses returned from commands.
replies = ["A message for you, sir!: ",
           "This just arrived via telegraph: ",
           "I need a vacation...",
           "*hmmpf*",
           "*an envelope slides in under the door*"]

# Deposit Prefixes; Charfred will use one of these as a prefix for
# posts that mention the commandCh.
deposits = ["Please follow me to the study, sir!",
            "Please follow me to the study, ma\'am!",
            "I have prepared the dungeon for you, sir!",
            "I have prepared the study for you, sir!",
            "The study is ready for you.",
            "GET TO THE CHOPPAH!"]
