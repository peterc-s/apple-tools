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

If you have two files `main.bas` and `other.bas` you can include `other.bas` in `main.bas`.

`main.bas`:
```BASIC
#INCLUDE "other.bas"

PRINT "Hello from main.bas"
GOSUB @OTHER_HELLO
END
```

`other.bas`:
```BASIC
<OTHER_HELLO> PRINT "Hello from other.bas"
RETURN
```

You can use the preprocessor on `main.bas` and you'll get:
```BASIC
0 GOTO 3
1 PRINT "Hello from other.bas"
2 RETURN
3 PRINT "Hello from main.bas"
4 GOSUB 1
5 END
```

Which should give you:
```
Hello from main.bas
Hello from other.bas
```

Which could have just been:
```BASIC
0 PRINT "Hello from main.bas"
1 PRINT "Hello from other.bas"
2 END
```

So you should use this feature sparingly and when it makes sense.

As for the current jank, there is no proper relative includes. For example:
```
.
|- main.bas
|- lib/
    |- lib.bas
    |- lib2.bas
```

If `lib.bas` had `#INCLUDE "lib2.bas"`, this would not work (assuming we passed `main.bas` to the preprocessor). `lib.bas` would instead need `#INCLUDE "lib/lib2.bas"`. This is because the include path always comes from the "main" file.

### Remark Removal
The preprocessor also removes remarks.
