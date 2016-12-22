/**
Core script to handle datatables, it will also handle updation of elements ( edit/delete)
**/
var ModalForm = function(api_url,modal,pagereload) {

    var _this = this;
    _this.api_url = api_url;
    //handling addition of new element
    $(document).on('click', '#'+modal+'-add-new', function(e){ 
        $('#'+modal+'-save-button').val('');
        resetformfields();
        $('#'+modal).modal();   
    });

    var repopulateform = function(formid,url) {
        this.formid = formid;
        this.url    = url;
        $.blockUI({target: "#"+modal+"-form",baseZ: 2000});
        $.ajaxSetup({
            timeout: 30000,
            error: function(xhr) {
                    $.unblockUI({target:"#"+modal+"-form"});
                    new ShowError('Error',"Network timeout!!,Please try again later");
                 }
         });        
        $.ajax({
            type: 'get',
            url: url,
            data: {},
            success: function(data) {
                $.unblockUI({target:"#"+modal+"-form"});
                if (data.status) {
                    $.each(data.data, function(name, val){
                        var $el = $('[name="'+name+'"]'),
                            type = $el.attr('type');

                        switch(type){
                            case 'checkbox':
                                $el.attr('checked', 'checked');
                                break;
                            case 'radio':
                                $el.filter('[value="'+val+'"]').attr('checked', 'checked');
                                break;
                            case 'HTMLInputElement':
                                //don't set HTMLinput element                                
                            default:
                                $el.val(val);
                        }
                    });
                
                }
                else{
                        new ShowError('Error',data.msg);
            
                }
            }
        });
    }

    var resetformfields = function(formid) {
        
        $('#'+formid).find('input:text, input:password, input:file, select, textarea').val('');
        $('#'+formid).find('input:radio, input:checkbox').removeAttr('checked').removeAttr('selected')
    
    }

    // handle saving
    $('#'+modal+'-save-button').click(function(e) {
        //setup timeout for Post and enable error display
        e.preventDefault();        
        id = $(this).val();

        // check if post or put needed
        if(id){
            method = "PUT";
            url = _this.api_url + id;


        }
        else{
            method = "POST";
            url = _this.api_url;
        }

        $.ajaxSetup({
            
            contentType : 'application/x-www-form-urlencoded',
           
         });
        //block UI while form is processed
        $.blockUI({target: "#"+modal,baseZ: 2000});
            //$('#'+modal).modal('hide');
        $.ajax({
            url: url,
            type: method ,
            data: $( "#"+modal+"-form" ).serialize(),
            contentType : 'application/x-www-form-urlencoded',
            timeout: 30000,
            success: function(data) {
                $.unblockUI("#"+modal);
                if(data.status){                    
                    new ShowSuccess('Success',data.msg);                    
                    $('#'+modal).modal('hide');
                    resetformfields();    
                    if (typeof pagereload != "undefined"){
                        location.reload();
                    }
                      
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

    //handle editing 
     $('#'+modal+'-edit').click(function(e) {
        e.preventDefault();  
        id = $(this).attr('value');
        url = _this.api_url + id;
        repopulateform("#"+modal+"-form",url);
        $('#'+modal+'-save-button').val(id);
        $('#'+modal).modal();       
    });



};
