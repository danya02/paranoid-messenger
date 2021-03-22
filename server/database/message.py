from .connection import create_table, MyModel
from .user import User
import peewee as pw
import enum

class MessageBlob(MyModel):
    """
    Represents an encrypted message blob in the blob store.

    This table exists to facilitate a single blob being used by multiple
    messages, as in a broadcast or a group chat.
    """

    path = pw.CharField(unique=True, verbose_name='Path to file in blob store',
        help_text='Relative path to content which can be '+\
        'decrypted with the session key.')

    size = pw.IntegerField(index=True, verbose_name='File size',
            help_text='Size of referenced file, in bytes. '+\
                    'Together with the upload time, used to'+\
                    'determine which files and messages to delete.')

    @classmethod
    def delete_orphans(cls):
        '''
        Delete orphaned blobs. Return (number of deleted files, total size).

        Should be run periodically to clear disk space.
        '''
        query = cls.select().\ # for every row in this table,
                join(Message, pw.JOIN.LEFT).\ # add the message referencing it
                where(Message.id.is_null()) # and return ones that have no match

        count = 0
        size = 0
        for row in query:
            # TODO: remove the file
            count += 1
            size += row.size
            row.delete_instance()

        return count, size

class MessageStatus(enum.IntEnum):
    CREATED = 0  # The message has just been uploaded to the server.
    
    NOTIFIED = 1  # The target's device has received the notification
                  # and is aware that there is a message waiting for download.
                  # It may have emitted a notification for the user.

    DELIVERED = 2  # The target's device has downloaded the message
                   # to its local storage. It will soon be deleted
                   # from the server's blob store.
                   # The device may have emitted a notification, or updated
                   # the notification from before to show the contents of the
                   # message.

    READ = 3  # The target user has navigated to this message in the app.
              # Note: depending on the user's privacy settings and the
              # target's capabilities, this may not be sent, and the fact
              # that this status is not being sent does not mean the user
              # has actually not read the message.

    ENTER_DELETION_LIST = 80  # The message has just started being considered
                              # for deletion before delivery. If applicable,
                              # it has also been resent to the target device.

    NEAR_END_DELETION_LIST = 85  # The message is very close to being deleted
                                 # without being delivered. If applicable,
                                 # it has also been resent to the target device.

    DELETED_WITHOUT_DELIVERY = 90  # The message has been deleted
                                   # without being delivered. If applicable,
                                   # a notification saying the message has been
                                   # deleted has been sent to the target device.



@create_table
class Message(MyModel):
    
    """
    Represents a message sent from one user to another, or to a group.
    """
    
    message_id = pw.BlobUUIDField(unique=True, verbose_name='Message UUID',
            help_text="This message's unique ID. This is set by the sender,"+\
            'kept track of by the server, and used to deduplicate '+\
            'messages by the receiver.')

    received_at = pw.DateTimeField(index=True,
            verbose_name='Message received by server at',
            help_text='When did the server finish storing the message? '+\
            '(For privacy or connectivity reasons, the message may '+\
            'arrive at the server at a different time to when it '+\
            'was composed -- timeouts should be computed based '+\
            'on time of reception, not of transmission.)'
            )

    sess_key = pw.BlobField(verbose_name='Session key',
            help_text='Encrypted session key, AKA content encryption key, '+\
            'for message blobs.')

    blob = pw.ForeignKeyField(MessageBlob, verbose_name='Message blob',
            help_text="Reference to this message's encrypted blob.")

    addressee = pw.ForeignKeyField(User, index=True,
            verbose_name='Message addressed to',
            help_text='What user should receive this message? '+\
            '(This is necessary to emit the correct push messages; '+\
            'the author of the message should be in the encrypted blob, '+\
            'along with an identity-confirming signature.)'
            )

