
NOTIFI_ALL_USERS        = 1
NOTIFI_ALL_ADMIN        = 2
NOTIFI_ALL_CLIENTS      = 3
NOTIFI_ALL_SUPER        = 4
NOTIFI_ONCE             = 5

NOTIFI_TYPE_DANGER      = 1
NOTIFI_TYPE_WARNING     = 2
NOTIFI_TYPE_INFO        = 3
NOTIFI_TYPE_SUCCESS     = 4

GUESTTRACK_PRELOGIN      = 1
GUESTTRACK_LOGIN         = 2
GUESTTRACK_POSTLOGIN     = 3
GUESTTRACK_AUTH          = 4
GUESTTRACK_POST_AUTH     = 5

LOGINAUTH_INIT      = 0
LOGINAUTH_FIRST     = 1 #means login completed once
LOGINAUTH_REPEATED  = 2 #means login completed more than once



AUTH_TYPE_BYPASS    = 0
AUTH_TYPE_SPLASH    = 0
AUTH_TYPE_EMAIL     = 1
AUTH_TYPE_VOUCHER   = 2
AUTH_TYPE_SOCIAL    = 4
AUTH_TYPE_SMS       = 8
AUTH_TYPE_PAYMENT   = 16
AUTH_TYPE_ACCOUNT   = 32
AUTH_TYPE_ALL       = 63

EXPORT_NONE         = 0
EXPORT_MAILCHIMP    = 1

PAYMENT_GW_NONE     = 0
PAYMENT_GW_STRIPE   = 1


TRANS_FREE_NOT_ELIGIBLE = 1
TRANS_FREE_OK = 2
TRANS_PAID_ERROR   = 3
TRANS_PAID_SUCCESS = 4
TRANS_PAID_AND_USED = 5
TRANS_REFUND_SUCCESS = 5


FORM_FIELD_FIRSTNAME    = 1
FORM_FIELD_LASTNAME     = 2
FORM_FIELD_EMAIL        = 4
FORM_FIELD_PHONE        = 8
FORM_FIELD_DOB          = 16
FORM_FIELD_EXTRA1       = 32
FORM_FIELD_EXTRA2       = 64
FORM_FIELD_ALL          = 127


MANDATE_FIELD_FIRSTNAME = 1
MANDATE_FIELD_LASTNAME  = 2
MANDATE_FIELD_EMAIL     = 4
MANDATE_FIELD_PHONE     = 8
MANDATE_FIELD_DOB       = 16
MANDATE_FIELD_EXTRA1    = 32
MANDATE_FIELD_EXTRA2    = 64

VALIDATE_FIELD_NONE    = 0
VALIDATE_FIELD_EMAIL   = 1
VALIDATE_FIELD_PHONE   = 2


REDIRECT_ORIG_URL   = 1
REDIRECT_CUSTOM_URL = 2

FACEBOOK_LIKE_OFF   = 1
FACEBOOK_LIKE_OPNL  = 2
FACEBOOK_LIKE_REQ   = 3

FACEBOOK_POST_OFF   = 1
FACEBOOK_POST_OPNL  = 2
FACEBOOK_POST_REQ   = 3


CLIENT_REPORT_NONE      = 1
CLIENT_REPORT_WEEKLY    = 2
CLIENT_REPORT_MONTHLY   = 3

font_list = ["Helvetica, sans-serif",
    "Verdana, sans-serif",
    "Gill Sans, sans-serif",
    "Avantgarde, sans-serif",
    "Helvetica Narrow, sans-serif",
    "Times, serif",
    "Times New Roman, serif",
    "Palatino, serif",
    "Bookman, serif",
    "New Century Schoolbook, serif",
    "Andale Mono, monospace",
    "Courier New, monospace",
    "Courier, monospace",
    "Lucidatypewriter, monospace",
    "Fixed, monospace",
    "Comic Sans, Comic Sans MS, cursive",
    "Zapf Chancery, cursive",
    "Coronetscript, cursive",
    "Florence, cursive",
    "Parkavenue, cursive",
    "Impact, fantasy",
    "Arnoldboecklin, fantasy",
    "Oldtown, fantasy",
    "Blippo, fantasy",
    "Brushstroke, fantasy",
    "MrsEavesXLSerNarOT-Reg",
    "Georgia, serif"]