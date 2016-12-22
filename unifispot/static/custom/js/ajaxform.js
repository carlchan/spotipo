/**
Core script to handle datatables, it will also handle updation of elements ( edit/delete)
**/
var AjaxForm = function(api_url,formid,id) {

    var _this = this;
    _this.api_url = api_url;
    if(id){
        _this.obj_url = api_url + id;
    }else{
        _this.obj_url =api_url;
    }
    
    //handling addition of new element
    $(document).on('click', '#'+formid+'-add-new', function(e){ 
        $('#'+formid+'-save-button').val('');
        resetformfields();
        $('#'+formid).modal();   
    });

    var repopulateform = function(formid,url) {
        this.formid = formid;
        this.url    = url;
        $.blockUI();
        $.ajaxSetup({
            timeout: 30000,
            error: function(xhr) {
                    $.unblockUI();
                    new ShowError('Error',"Network timeout!!,Please try again later");
                 }
         });        
        $.ajax({
            type: 'get',
            url: url,
            data: {},
            success: function(data) {
                $.unblockUI();
                if (data.status) {
                    $.each(data.data, function(name, val){
                        var $el = $('#'+formid+' #'+name),
                            type = $el.attr('type');


                        switch(type){
                            case 'checkbox':
                                if(val){
                                    $el.attr('checked', 'checked');
                                    $("input[type='checkbox']").trigger('change');
                                }
                                break;
                            case 'radio':
                                if(val){
                                    $el.filter('[value="'+val+'"]').attr('checked', 'checked');
                                    $el.trigger( "change" );
                                }
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
    $('#'+formid+'-save-button').click(function(e) {
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
        $.blockUI();

        $.ajax({
            url: url,
            type: method ,
            data: $( "#"+formid ).serialize(),
            contentType : 'application/x-www-form-urlencoded',
            timeout: 30000,
            success: function(data) {
                $.unblockUI();
                if(data.status){                    
                    new ShowSuccess('Success',data.msg);                    
  
                    
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

    //handle editing 
     $('#'+formid+'-edit').click(function(e) {
        e.preventDefault();  
        id = $(this).attr('value');
        url = _this.api_url + id;
        repopulateform("#"+formid+"-form",url);
        $('#'+formid+'-save-button').val(id);
    
    });


    repopulateform(formid,_this.obj_url);

};
