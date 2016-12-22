/**
Core script to module forms, opens up a modal and load content from URL
**/
var ModuleForm = function(api_url,modal,configbutton) {

    var _this = this;
    _this.api_url = api_url;
    //handling addition of new element
    $(document).on('click', '#'+configbutton, function(e){ 
        $('#'+modal+'-save-button').val(api_url);
        repopulateform(api_url);
        $('#'+modal).modal();   
    });

    var repopulateform = function(url) {
        this.url    = url;
        $.blockUI({target: "#"+modal+"-form",baseZ: 2000});
        $.ajaxSetup({
            timeout: 30000,
            error: function(xhr) {
                    $.unblockUI({target:"#"+modal+"-form"});
                    new ShowError('Error',"Network timeout!!,Please try again later");
                 }
         });    

        $('#'+modal+'-form-body').load(url, 
                function( response, status, xhr ) {
                $.unblockUI({target:"#"+modal+"-form"});

        });             
    }





};

var ModuleGeneralForm = function(modal) {


    // handle saving
    $('#'+modal+'-save-button').click(function(e) {
        //setup timeout for Post and enable error display
        e.preventDefault();        
        url = $(this).val();
        method = "POST";



        $.ajaxSetup({
            
            contentType : 'application/x-www-form-urlencoded',
           
         });
        //block UI while form is processed
        $.blockUI({target: "#"+modal,baseZ: 2000});
            //$('#'+modal).modal('hide');
        $.ajax({
            url: url,
            type: method ,
            data: $( "#"+modal+'-form-body :input' ).serialize(),
            contentType : 'application/x-www-form-urlencoded',
            timeout: 30000,
            success: function(data) {
                console.log(data);
                $.unblockUI("#"+modal);
                if(data.status){                    
                    new ShowSuccess('Success',data.msg);                    
                    $('#'+modal).modal('hide');
                    
                }
                else{
                    new ShowError('Error',data.msg);
                    $('#'+modal).modal();
                }
            },
            dataType:'json',// I expect a JSON response
            error: function(xhr) {
                    $.unblockUI("#"+modal);
                    new ShowError('Error',"Network timeout!!,Please try again later");
                    
            }
        });

        return false;
    });




};
