#import time
#import hashlib
from django.conf import settings
#from django.http import Http404
from django.core.urlresolvers import reverse
from forms import PayflowLinkPaymentForm
from payments.models import Payment
from payments.utils import payment_processing_object_updates
from event_logs.models import EventLog
from notification.utils import send_notifications

#from site_settings.utils import get_setting


def prepare_payflowlink_form(request, payment):
    amount = "%.2f" % payment.amount
    
    params = {
              'login':settings.PAYPAL_MERCHANT_LOGIN,
              'partner': settings.PAYFLOWLINK_PARTNER,
              'amount':amount,
              'type': 'A',
              'showconfirm': 'True',
              'disablereceipt': 'False',
              'custid': payment.id,
              'name':'%s %s' % (payment.first_name, payment.last_name),
              'email': payment.email,
              'address': '%s %s' % (payment.address, payment.address2),
              'city': payment.city,
              'state': payment.state,
              'country': payment.country,
              'fax':payment.fax,
              'phone':payment.phone,
              'nametoship': '%s %s' % (payment.ship_to_first_name, payment.ship_to_last_name),
              'addresstoship': payment.ship_to_address,
              'citytoship': payment.ship_to_city,
              'statetoship': payment.ship_to_state,
              'ziptoship': payment.ship_to_zip,
              'countrytoship': payment.ship_to_country,
        
        }
    form = PayflowLinkPaymentForm(initial=params)
    
    return form

def payflowlink_thankyou_processing(request, response_d, **kwargs):
    from django.shortcuts import get_object_or_404
    response_d = dict(map(lambda x: (x[0].lower(), x[1]), response_d.items()))

    paymentid = response_d.get('custid', 0)
    try:
        paymentid = int(paymentid)
    except:
        paymentid = 0
    payment = get_object_or_404(Payment, pk=paymentid)
    processed = False
    
    if payment.invoice.balance > 0:     # if balance==0, it means already processed
        payment_update_payflowlink(request, response_d, payment)
        payment_processing_object_updates(request, payment)
        processed = True
        
        # log an event
        if payment.response_code == '1':
            event_id = 282101
            description = '%s edited - credit card approved ' % payment._meta.object_name
        else:
            event_id = 282102
            description = '%s edited - credit card declined ' % payment._meta.object_name
            
        log_defaults = {
            'event_id' : event_id,
            'event_data': '%s (%d) edited by %s' % (payment._meta.object_name, payment.pk, request.user),
            'description': description,
            'user': request.user,
            'request': request,
            'instance': payment,
        }
        EventLog.objects.log(**log_defaults)
        
        notif_context = {
        'request': request,
        'object': payment,
        }

        send_notifications('module','payments', 'paymentrecipients',
            'payment_added', notif_context)
        
    return payment, processed
        
def payment_update_payflowlink(request, response_d, payment, **kwargs):
    payment.address = response_d.get('address', '')
    payment.city = response_d.get('city', '')
    payment.state = response_d.get('state', '')
    payment.country = response_d.get('country', '')
    payment.phone = response_d.get('phone', '')
    sname = response_d.get('nametoship', '')
    if sname:
        name_list = sname.split(' ')
        if len(name_list) >= 2:
            payment.ship_to_first_name = name_list[0]
            payment.ship_to_last_name = ' '.join(name_list[1:])
    payment.ship_to_address = response_d.get('addresstoship', '')
    payment.ship_to_city = response_d.get('citytoship', '')
    payment.ship_to_state = response_d.get('statetoship', '')
    payment.ship_to_zip = response_d.get('ziptoship', '')
    payment.ship_to_country = response_d.get('countrytoship', '')
    
    result = response_d.get('result', '')
    respmsg = (response_d.get('respmsg', '')).lower()
    payment.response_reason_text = respmsg
    
    if result=='0' and  respmsg == 'approved':
        payment.response_code = '1'
        payment.response_subcode = '1'
        payment.response_reason_code = '1'
        payment.status_detail = 'approved'
        # http://www.firstdata.com/downloads/marketing-merchant/fd_globalgatewayconnect_usermanualnorthamerica.pdf
        payment.trans_id = response_d.get('pnref', '')
    else:
        payment.response_code = 0
        payment.response_reason_code = 0
    
    
    if payment.is_approved:
        payment.mark_as_paid()
        payment.save()
        payment.invoice.make_payment(request.user, payment.amount)
    else:
        if not payment.status_detail:
            payment.status_detail = 'not approved'
        payment.save()
            
    
    
    