function create_site_menu(url,siteid){

    $('#sitelist').html('');
    var sites = '';
    var site_head = '';
    $.ajax({
        type: 'get',
        url: url,
        data: {},
        success: function(data) {
            if (data.status) {
                $.each(data.data, function (i, item) {                   

                    if(siteid == item.id){
                        site_head = '<a href="javascript:;" class="user-profile dropdown-toggle" data-toggle="dropdown" aria-expanded="false"><strong>'+item.name+'</strong><span class=" fa fa-angle-down"></span></a>';

                    }
                    else{
                        sites = sites + '<li><a href="'+item.url+'">'+item.name+'</a></li>';
                    }

                });
                if(siteid == 0){

                    site_head = '<a href="javascript:;" class="user-profile dropdown-toggle" data-toggle="dropdown" aria-expanded="false"><strong>Dashboard</strong><span class=" fa fa-angle-down"></span></a>';

                }
                else{
                    //add site delete button
                    $('#sitedelete').html('<a href="#" id="site-del"  ><i class="fa fa-close" style="color:red;"></i></a>');
                    sites = sites+ '<li><a href="/">Dashboard</a></li>';

                }
                site_list_html = site_head+'<ul class="dropdown-menu dropdown-usermenu pull-right">'+sites;
                site_list_html = site_list_html +'<li><a href="#" id="newsitemodal-add-new" class="add"><strong>Add New Site</strong></a></li></ul>';                

                $('#sitelist').html(site_list_html);
            }
            else{
                new ShowError('Error',data.msg);             
            }
        }
    });

}
