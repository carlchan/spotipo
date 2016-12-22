/**
Core script to handle Notification .
**/
var ShowInfo = function(title,text) {

        pnnotify = new PNotify({
          title: title,
          type: "info",
          text: text,
          styling: 'bootstrap3',
          delay: 3000,

        });
        return pnnotify

};

var ShowNotice = function(title,text) {

        pnnotify =  new PNotify({
          title: title,
          type: "notice",
          text: text,
          styling: 'bootstrap3',
          delay: 3000,

        });
        return pnnotify

};

var ShowError = function(title,text) {

        pnnotify = new PNotify({
          title: title,
          type: "error",
          text: text,
          styling: 'bootstrap3',
          delay: 3000,

        });
        return pnnotify

};

var ShowSuccess = function(title,text) {

        pnnotify =  new PNotify({
          title: title,
          type: "success",
          text: text,
          styling: 'bootstrap3',
          delay: 3000,

        });
        return pnnotify

};


$(document).ready(function() {
 
    $('.close-notification').click(function(e) {
        //setup timeout for Post and enable error display
        e.preventDefault();        
        id = $(this).attr('id');
        $.ajaxSetup({
            type: 'PUT',
            timeout: 30000,
            error: function(xhr) {
                    $.unblockUI();
                    new ShowError('Error',"Network timeout!!,Please try again later");
                    
                 }
         });
        $.ajax({
            url: '/notifications/'+id,
            type: 'PUT' ,
            timeout: 30000,
            success: function(data) {
                $.unblockUI();
                if(data.status){                    
                    $('#notification-'+id).hide();                    
  
                    
                }
                else{
                    new ShowError('Error',data.msg);

                }
            },
            dataType:'json',// I expect a JSON response
            error: function(xhr) {
                    $.unblockUI();
                    new ShowError('Error',"Network timeout!!,Please try again later");
                    
            }
        });        

        return false;
    });

        
});