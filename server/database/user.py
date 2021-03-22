from .connection import create_table, MyModel

@create_table
class User(MyModel):
    """
    Represents a single "user" -- a messaging and discovery unit.

    This does not need to be a single person.
    Rather, this is an identity -- a public key with a username.
    This is called a "User" for clarity.
    """

    class Meta:
        # A user must have either a username or a wordlist identifier.
        constraints = [pw.Check('(username IS NOT NULL) '+\
                'or (wordlist_id IS NOT NULL)')]

    username = pw.CharField(unique=True, null=True,
            verbose_name='Username',
            help_text="User's chosen identifier. Used for finding users. "+\
            "Can be changed at user's request."
        )
    
    username_lookup_allowed = pw.BooleanField(
            verbose_name='Lookup by username allowed',
            help_text='Should this user be shown in searches by username?'
        )

    wordlist_id = pw.IntegerField(unique=True, null=True,
            verbose_name='ID by wordlist',
            help_text="Alternative identifier for user based on a wordlist. "+\
            "Can be regenerated, but not set."
            )

    uid = pw.BinaryUUIDField(unique=True, default=uuid.uuid4,
            verbose_name='User UUID',
            help_text='Public-facing unique user ID, '+\
                    'distinct from the database ID. '+\
            'Can always be used to find a user, regardless of settings.'+\
            'Should be stored persistently by clients.'+\
            'Once generated, cannot be changed.')


    public_key = pw.BlobField(
            verbose_name='Public key',
            help_text='Used to encrypt data to send this user.'
            # TODO: figure out if it is feasible to allow for this to be changed
        )

    algorithm = None # TODO: find a way to support multiple algorithms


