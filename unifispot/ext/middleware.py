from unifispot.version import version
from unifispot.core.const import font_list
from unifispot.core.models import Notification


def configure(app):
    #inject font lists
    @app.template_filter()
    def printfont(value):        
        return font_list[value]

    #create test to check if a fieldname 
    #in siteform points to a login method
    @app.template_test('is_login_method')
    def is_login_method(fieldname):
        loginmethods = app.config['GUESTLOGIN_MODULES']          
        if fieldname.split('_')[0] == 'auth' and \
                fieldname.split('_')[1] in loginmethods:
            return True
        else:
            return False
                
    @app.template_filter()
    def toint(value):
        '''Return the value if its not None else return 0

        useful when displaying numbers
        '''
        if value:
            return value
        else:
            return 0
        
    @app.template_filter()
    def tostring(value):
        '''Return the value if its not None else return emptry string

        useful when displaying strings
        '''   
        if value:
            return value
        else:
            return ''       

    # Template filters.
    @app.template_filter()
    def print_version(text):
        return '%s %s'%(text,version)                       

    # Template filters.
    @app.template_filter()
    def show_notifications(user):
        notifications = []
        notifications = Notification.get_user_notifications(user.account_id,user.id)
        if user.check_admin():
            notifications.extend(Notification.get_common_notifications(user.account_id))
        notify_text = ''
        for notify in notifications:
            notify_text +='''<div class="alert alert-%s alert-dismissable" id="notification-%s">
                <button aria-hidden="true" data-dismiss="alert" id="%s" class="close close-notification" type="button">x</button>
                %s
            </div>'''%(notify.get_type(),notify.id,notify.id,notify.content)
        return notify_text        