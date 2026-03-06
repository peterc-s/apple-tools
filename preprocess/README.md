# Super Basic Applesoft BASIC Preprocessor
A poorly written but functional BASIC preprocessor for making life less painful when trying to write Applesoft BASIC.

## Usage
You will need `astral-uv` if you want to run this without pain.

To see options:
```sh
uv run preprocess --help
```

## Features
### Automatic Numbering
Never write numbers by your lines and have to shift them around ever again!

Turns:
```BASIC
PRINT "HELLO"
PRINT "WORLD"
```

Into:
```BASIC
0 PRINT "HELLO"
1 PRINT "WORLD"
```

### Labels
Automatic numbering on its own isn't that big of a deal. Introducing: labels.

Turns:
```BASIC
<HELLO> PRINT "HELLO"
GOTO @HELLO
```

Into:
```BASIC
0 PRINT "HELLO"
1 GOTO 0
```

### Multi-file Projects
This one is super janky currently (but it does work).

The file you pass in to the preprocessor is the "main" file, the first executable line in the "main" file
will be made the entrypoint. You can also define your own entrypoint in the "main" file by adding `:ENTRY:` to the start of it.

If you have two files `main.apl` and `other.apl` you can include `other.apl` in `main.apl`.

`main.apl`:
```BASIC
#INCLUDE "other.apl"

PRINT "Hello from main.apl"
GOSUB @OTHER_HELLO
END
```

`other.apl`:
```BASIC
<OTHER_HELLO> PRINT "Hello from other.apl"
RETURN
```

You can use the preprocessor on `main.apl` and you'll get:
```BASIC
0 GOTO 3
1 PRINT "Hello from other.apl"
2 RETURN
3 PRINT "Hello from main.apl"
4 GOSUB 1
5 END
```

Which should give you:
```
Hello from main.apl
Hello from other.apl
```

Which could have just been:
```BASIC
0 PRINT "Hello from main.apl"
1 PRINT "Hello from other.apl"
2 END
```

So you should use this feature sparingly and when it makes sense.

As for the current jank, there is no proper relative includes. For example:
```
.
|- main.apl
|- lib/
    |- lib.apl
    |- lib2.apl
```

If `lib.apl` had `#INCLUDE "lib2.apl"`, this would not work (assuming we passed `main.apl` to the preprocessor). `lib.apl` would instead need `#INCLUDE "lib/lib2.apl"`. This is because the include path always comes from the "main" file.

