from flask.ext.wtf import Form
from wtforms import TextField, validators, HiddenField

class EnterDBInfo(Form):
    dbNotes = TextField(label='Items to add to DB', description="db_enter", validators=[validators.required(), validators.Length(min=0, max=128, message=u'Enter 128 characters or less')])    
    fld2 = HiddenField( 'value' )

