/**
Core script to handle datatables, it will also handle updation of elements ( edit/delete)
**/
var DataTableWithEdit = function(table_id,datatable_config,api_url,modal,pagereload) {

    var _this = this;
    _this.api_url = api_url;
    var data_table = $("#"+table_id).DataTable(datatable_config);    

    //handling addition of new element
    $('#'+modal+'-add-new').click(function(e) {
            $('#'+modal+'-save-button').val('');
            $("#role-form-group").show();
            resetformfields(modal+"-form");
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
                    else{
                        data_table.ajax.reload();    
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
    $('#'+table_id).on( 'click', 'a.edit', function (e) {
        e.preventDefault();  
        id = $(this).attr('id');
        url = _this.api_url + id;
        repopulateform("#"+modal+"-form",url);
        $('#'+modal+'-save-button').val(id);
        $('#'+modal).modal();       
    });

    //handle deleting 
    $('#'+table_id).on( 'click', 'a.delete', function (e) {
        el = this;
        bootbox.confirm("You are about to delete an element,this action can't be undone. Are you Sure? ", function(r) {
            if (r) {
                //sent request to delete order with given id
                //block UI while request is processed
                $.blockUI({boxed: true});
                $.ajax({
                    type: 'delete',
                    url: _this.api_url + el.id,
                    data: {},
                    success: function(b) {
                         $.unblockUI();
                        if (b.status) {
                            new ShowSuccess('Success',b.msg);  
                            data_table.ajax.reload();                        
                        }
                        else{
                            new ShowError('Error',b.msg);
                        }                                               
                    },
                    timeout: 30000,
                    error: function(xhr) {
                        $.unblockUI();
                        new ShowError('Error',"Network timeout!!,Please try again later");
                    }
                    
                });
            
            }
        });
    
    });
    //handle refresh
    $('#'+modal+'-refresh-button').click(function(e) {
        data_table.ajax.reload();
    });

};
