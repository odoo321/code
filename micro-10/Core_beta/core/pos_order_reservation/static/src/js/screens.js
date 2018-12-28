odoo.define('pos_order_reservation.screens', function (require) {
	var screens = require('point_of_sale.screens');
	var gui = require('point_of_sale.gui');
	var Model = require('web.DataModel');
	var utils = require('web.utils');
	var PopupWidget = require('point_of_sale.popups');
	var models = require('point_of_sale.models');
	
	var core = require('web.core');
	var QWeb = core.qweb;
	var round_pr = utils.round_precision;
	var _t = core._t;
	
	var ShowOrderList = screens.ActionButtonWidget.extend({
	    template : 'ShowOrderList',
	    button_click : function() {
	        self = this;
	        self.gui.show_screen('orderlist');
	    },
	});

	screens.define_action_button({
	    'name' : 'showorderlist',
	    'widget' : ShowOrderList,
	    'condition': function(){
	        return this.pos.config.enable_order_reservation
	    },
	});
	
	var ReservationMode = screens.ActionButtonWidget.extend({
	    template : 'ReservationMode',
	    button_click : function() {
	        var self = this;
	        var order = self.pos.get_order();
	        order.set_reservation_mode(!order.get_reservation_mode());
	        order.get_reservation_mode() ? this.$el.addClass('highlight') : this.$el.removeClass('highlight')
	    },
	});

	screens.define_action_button({
	    'name' : 'ReservationMode',
	    'widget' : ReservationMode,
	    'condition': function(){
	        return this.pos.config.enable_order_reservation
	    },
	});

    var SaveDraftButton = screens.ActionButtonWidget.extend({
	    template : 'SaveDraftButton',
	    button_click : function() {
	        var self = this;
            var selectedOrder = this.pos.get_order();
            selectedOrder.initialize_validation_date();
            var currentOrderLines = selectedOrder.get_orderlines();
            var orderLines = [];
            var client = selectedOrder.get_client();
            _.each(currentOrderLines,function(item) {
                return orderLines.push(item.export_as_JSON());
            });
            if (orderLines.length === 0) {
                return alert ('Please select product !');
            } else {
            	if(!selectedOrder.get_client()){
            		self.gui.show_screen('clientlist');
            		return
            	}
                var credit = selectedOrder.get_total_with_tax() - selectedOrder.get_total_paid();
        		if (client && credit > client.remaining_credit_limit){
                    self.gui.show_popup('max_limit',{
                        remaining_credit_limit: client.remaining_credit_limit,
                        draft_order: true,
                    });
                    return
        	    } else {
                    this.pos.push_order(selectedOrder);
                    self.gui.show_screen('receipt');
                }
            }
	    },
	});

    screens.define_action_button({
	    'name' : 'savedraftbutton',
	    'widget' : SaveDraftButton,
	    'condition': function(){
	        return this.pos.config.allow_reservation_with_no_amount;
	    },
	});

	/* Order list screen */
	var OrderListScreenWidget = screens.ScreenWidget.extend({
	    template: 'OrderListScreenWidget',

	    init: function(parent, options){
	    	var self = this;
	        this._super(parent, options);
	        this.reload_btn = function(){
	        	$('.fa-refresh').toggleClass('rotate', 'rotate-reset');
	        	if($('#select_draft_orders').prop('checked')){
            		$('#select_draft_orders').click();
            	}
	        	self.reloading_orders();
	        };
	    },

	    filter:"all",

        date: "all",

	    start: function(){
	    	var self = this;
            this._super();
            
            this.$('.back').click(function(){
                self.gui.show_screen('products');
            });

            var orders = self.pos.get('pos_order_list');
            this.render_list(orders);

            $('input#datepicker').datepicker({
           	    dateFormat: 'yy-mm-dd',
                autoclose: true,
                closeText: 'Clear',
                showButtonPanel: true,
                onSelect: function (dateText, inst) {
                	var date = $(this).val();
					if (date){
					    self.date = date;
					    self.render_list(self.pos.get('pos_order_list'));
					}
				},
				onClose: function(dateText, inst){
                    if( !dateText ){
                        self.date = "all";
                        self.render_list(self.pos.get('pos_order_list'));
                    }
                }
            }).focus(function(){
                var thisCalendar = $(this);
                $('.ui-datepicker-close').click(function() {
                    thisCalendar.val('');
                    self.date = "all";
                    self.render_list(self.pos.get('pos_order_list'));
                });
            });

//			$('input#datepicker').datepicker({
//           		'dateFormat': 'yy-mm-dd',
//               'autoclose': true,
//               onSelect: function (dateText, inst) {
//                	var date = $(this).val();
//					if (date){
//					    self.date = date;
//					    self.render_list(orders);
//					}
//				}
//           });

            //button draft
            this.$('.button.reserved').click(function(){
            	if(self.$(this).hasClass('selected')){
	        		self.$(this).removeClass('selected');
	        		self.filter = "all";
        		}else{
        			self.$(this).addClass('selected');
	        		self.filter = "reserved";
        		}
        		self.render_list(self.pos.get('pos_order_list'));
            });

			this.$('.order-list-contents').delegate('.order-line td:not(.order_history_button)','click', function(event){
                var order_id = parseInt($(this).parent().data('id'));
                self.gui.show_screen('orderdetail', {'order_id': order_id});
			});

            //Pay due Amount
            this.$('.order-list-contents').delegate('#pay_due_amt','click',function(event){
            	var order_id = parseInt($(this).data('id'));
            	self.pay_order_due(order_id);

            });

            this.$('.order-list-contents').delegate('#cancel_order','click', function(event){
                var order = self.pos.get_order();
                var order_id = parseInt($(this).data('id'));
                var result = self.pos.db.get_order_by_id(order_id);

                self.gui.show_popup("cancel_order_popup", { 'order': result });
            });

            this.$('.order-list-contents').delegate('#delivery_date','click', function(event){
                var order = self.pos.get_order();
                var order_id = parseInt($(this).data('id'));
                var result = self.pos.db.get_order_by_id(order_id);
                order.set_delivery_date(result.delivery_date);
                self.gui.show_popup("delivery_date_popup", { 'order': result, 'new_date': false });
            });

          //search box
            var search_timeout = null;
            if(this.pos.config.iface_vkeyboard && self.chrome.widget.keyboard){
            	self.chrome.widget.keyboard.connect(this.$('.searchbox input'));
            }
            this.$('.searchbox input').on('keyup',function(event){
                $(this).autocomplete({
                    source: self.search_list,
                    select: function (a, b) {
                        self.perform_search(b.item.value, true);
                    }
                })
                clearTimeout(search_timeout);
                var query = this.value;
                search_timeout = setTimeout(function(){
                    self.perform_search(query, event.which === 13);
                },70);
            });

            this.$('.searchbox .search-clear').click(function(){
                self.clear_search();
            });
            
	    },
	    pay_order_due: function(order_id){
	        var self = this;
	        var result = self.pos.db.get_order_by_id(order_id);
	        if(!result){
	            new Model('pos.order').call('search_read', [[['id', '=', order_id], ['state', 'not in', ['draft']]]])
	            .then(function(order){
	                if(order && order[0])
	                    result = order[0]
	            });
	        }
            if(result.state == "paid"){
                alert("Sorry, This order is paid State");
                return
            }
            if(result.state == "done"){
                alert("Sorry, This Order is Done State");
                return
            }
            if (result && result.lines.length > 0) {
                var count = 0;
                var selectedOrder = self.pos.get_order();
                var currentOrderLines = selectedOrder.get_orderlines();
                if(currentOrderLines.length > 0) {
                    for (var i=0; i <= currentOrderLines.length + 1; i++) {
                        _.each(currentOrderLines,function(item) {
                            currentOrderLines.remove_orderline(item);
                        });
                    }
                    for (var i=0; i <= currentOrderLines.length + 1; i++) {
                        _.each(currentOrderLines,function(item) {
                            currentOrderLines.remove_orderline(item);
                        });
                    }
                }
                if (result.partner_id && result.partner_id[0]) {
                    var partner = self.pos.db.get_partner_by_id(result.partner_id[0])
                }
                if(!result.partial_pay){
                    selectedOrder.set_reservation_mode(true);
                }
                selectedOrder.set_delivery_date(result.delivery_date);
                selectedOrder.set_client(partner);
                selectedOrder.set_pos_reference(result.pos_reference);
                selectedOrder.set_paying_due(true);
                if (result.lines) {
                        new Model("pos.order.line").get_func("search_read")([['id', 'in', result.lines]], []).then(
                            function(results) {
                             if(results){
                                 _.each(results, function(res) {
                                     var product = self.pos.db.get_product_by_id(Number(res.product_id[0]));
                                     if(product){
                                         var line = new models.Orderline({}, {pos: self.pos, order: selectedOrder, product: product});
                                         line.set_discount(res.discount);
                                         line.set_quantity(res.qty);
                                         line.set_unit_price(res.price_unit);
                                         selectedOrder.add_orderline(line);
                                         selectedOrder.select_orderline(selectedOrder.get_last_orderline());
                                     }
                                 });
                                var prd = self.pos.db.get_product_by_id(self.pos.config.prod_for_payment[0]);
                                if(prd && result.amount_due > 0){
                                    var paid_amt = result.amount_total - result.amount_due;
                                    selectedOrder.set_amount_paid(paid_amt);
                                    selectedOrder.add_product(prd,{'price':-paid_amt});
                                }
                                self.gui.show_screen('payment');
                             }
                        });
                     selectedOrder.set_order_id(order_id);
                }
                selectedOrder.set_sequence(result.name);
            }
	    },
	    show: function(){
	        this._super();
	        this.reload_orders();
	        $('.button.reserved').removeClass('selected').trigger('click');
	    },
	    perform_search: function(query, associate_result){
	        var self = this;
            if(query){
				var orders = this.pos.db.search_order(query);
				self.render_list(orders);
            }else{
                var orders = self.pos.get('pos_order_list');
                this.render_list(orders);
            }
        },
        clear_search: function(){
            var orders = this.pos.get('pos_order_list');
            this.render_list(orders);
            this.$('.searchbox input')[0].value = '';
            this.$('.searchbox input').focus();
        },
	    render_list: function(orders){
        	var self = this;
            var contents = this.$el[0].querySelector('.order-list-contents');
            contents.innerHTML = "";
            var temp = [];
            if(self.filter !== "" && self.filter !== "all"){
	            orders = $.grep(orders,function(order){
	            	return order.reserved;
	            });
            }
            if(self.date !== "" && self.date !== "all"){
            	var x = [];
            	for (var i=0; i<orders.length;i++){
                    var date_order = $.datepicker.formatDate("yy-mm-dd",new Date(orders[i].date_order));
            		if(self.date === date_order){
            			x.push(orders[i]);
            		}
            	}
            	orders = x;
            }
            for(var i = 0, len = Math.min(orders.length,1000); i < len; i++){
                var order    = orders[i];
                order.amount_total = parseFloat(order.amount_total).toFixed(2); 
            	var clientline_html = QWeb.render('OrderlistLine',{widget: this, order:order});
                var clientline = document.createElement('tbody');
                clientline.innerHTML = clientline_html;
                clientline = clientline.childNodes[1];
                contents.appendChild(clientline);
            }
            $("table.order-list").simplePagination({
				previousButtonClass: "btn btn-danger",
				nextButtonClass: "btn btn-danger",
				previousButtonText: '<i class="fa fa-angle-left fa-lg"></i>',
				nextButtonText: '<i class="fa fa-angle-right fa-lg"></i>',
				perPage:self.pos.config.record_per_page > 0 ? self.pos.config.record_per_page : 10
			});
        },
        reload_orders: function(){
        	var self = this;
            var orders = self.pos.get('pos_order_list');
            this.search_list = []
            _.each(self.pos.partners, function(partner){
                self.search_list.push(partner.name);
            });
            _.each(orders, function(order){
                self.search_list.push(order.display_name, order.pos_reference)
            });
            this.render_list(orders);
        },
	    reloading_orders: function(){
	    	var self = this;
	    	return new Model('pos.order').get_func('ac_pos_search_read')
	    	(self.pos.domain_order)
	    	.then(function(result){
	    		self.pos.db.add_orders(result);
	    		self.pos.set({ 'pos_order_list' : result });
	    		self.reload_orders();
	    		return self.pos.get('pos_order_list');
	    	}).fail(function (error, event){
               if(error.code === 200 ){    // Business Logic Error, not a connection problem
              	self.gui.show_popup('error-traceback',{
                      message: error.data.message,
                      comment: error.data.debug
                  });
              }
              // prevent an error popup creation by the rpc failure
              // we want the failure to be silent as we send the orders in the background
              event.preventDefault();
              var orders=self.pos.get('pos_order_list');
      	        self.reload_orders();
      	        return orders
              });
	    },
	    renderElement: function(){
	    	var self = this;
	    	self._super();
	    	self.el.querySelector('.button.reload').addEventListener('click', this.reload_btn);
	    },
	});
	gui.define_screen({name:'orderlist', widget: OrderListScreenWidget});
	
	screens.PaymentScreenWidget.include({
        partial_payment: function() {
            var self = this;
            var currentOrder = this.pos.get_order();
            var client = currentOrder.get_client() || false;

            if(currentOrder.get_total_with_tax() > 0 && currentOrder.get_due() != 0){
				if(currentOrder.get_total_with_tax() > currentOrder.get_total_paid()
        			&& currentOrder.get_total_paid() != 0){
					var credit = currentOrder.get_total_with_tax() - currentOrder.get_total_paid();
					if (client && credit > client.remaining_credit_limit && !currentOrder.get_paying_due() && !currentOrder.get_cancel_order()){
						self.gui.show_popup('max_limit',{
							remaining_credit_limit: client.remaining_credit_limit,
							payment_obj: self,
						});
						return
					}
        	    }
            	if(currentOrder.get_reservation_mode() && !currentOrder.get_paying_due() && !currentOrder.get_cancel_order() && self.pos.config.enable_pos_welcome_mail){
            		currentOrder.set_fresh_order(true);
            	}
            	if(!currentOrder.get_reservation_mode()){
            	    currentOrder.set_partial_pay(true);
            	} else {
            	    currentOrder.set_draft_order(true);
            	}
				if(!currentOrder.get_delivery_date()){
					self.gui.show_popup("delivery_date_popup", { 'payment_obj': self, 'new_date': true });
				} else {
					if(currentOrder.get_total_paid() != 0){
						this.finalize_validation();
					}
					$('.js_reservation_mode').removeClass('highlight');
				}
        	}
        },
        renderElement: function() {
            var self = this;
            this._super();
            this.$('#partial_pay').click(function(){
            	if(self.pos.get_order().get_client()){
                	self.partial_payment();
                } else {
                	self.gui.show_screen('clientlist');
                }
            });
        },
        order_changes: function(){
            var self = this;
            this._super();
            var order = this.pos.get_order();
            var total = order ? order.get_total_with_tax() : 0;
            if(!order){
            	return
            } else if(order.get_due() == total || order.get_due() == 0){
            	self.$('#partial_pay').removeClass('highlight');
            } else {
            	self.$('#partial_pay').addClass('highlight');
            }
        },
        validate_order: function(force_validation){
        	this.pos.get_order().set_reservation_mode(false);
        	this._super(force_validation);
        },
        show: function(){
            var self = this;
            self._super();
            var order = self.pos.get_order();
            if(order.get_reservation_mode()){
                self.$('#partial_pay').show();
            } else {
                self.$('#partial_pay').text("Partial Pay");
            }
            if(order.get_total_with_tax() > 0){
                if((order.get_paying_due() || order.get_cancel_order())){
                    self.$('#partial_pay, .next').show();
                }
            } else {
                self.$('#partial_pay').hide();
                self.$('.next').show();
            }
            if((order.get_paying_due() || order.get_cancel_order())){
                self.$('#partial_pay').text("Pay");
            }
        },
        click_back: function(){
	        var self = this;
	        var order = this.pos.get_order();
	        if(order.get_paying_due() || order.get_cancel_order()){
                this.gui.show_popup('confirm',{
                    title: _t('Discard Sale Order'),
                    body:  _t('Do you want to discard the payment of POS '+ order.get_pos_reference() +' ?'),
                    confirm: function() {
                        order.finalize();
                    },
                });
	        } else {
	            self._super();
	        }
	    },
	    click_invoice: function(){
	        var order = this.pos.get_order();
	        if(order.get_cancel_order() || order.get_paying_due()){
	            return
	        }
	        this._super();
	    },
	    click_set_customer: function(){
	        var order = this.pos.get_order();
	        if(order.get_cancel_order() || order.get_paying_due()){
	            return
	        }
	        this._super();
	    },
    });
	
	screens.OrderWidget.include({
		set_value: function(val) {
			var order = this.pos.get_order();
			var line = order.get_selected_orderline();
	    	if ($.inArray(line && line.get_product().id,
	    	    [this.pos.config.prod_for_payment[0],
	    	    this.pos.config.refund_amount_product_id[0],
	    	    this.pos.config.cancellation_charges_product_id[0]]) == -1) {
	    		this._super(val)
	    	}
		},
	});

    var OrderDetailScreenWidget = screens.ScreenWidget.extend({
	    template: 'OrderDetailScreenWidget',
	     init: function(parent, options){
	        var self = this;
	        self._super(parent, options);
	    },
        show: function(){
            var self = this;
            self._super();

            var order = self.pos.get_order();
            var params = order.get_screen_data('params');
            var order_id = false;
            if(params){
                order_id = params.order_id;
            }
            if(order_id){
                self.clicked_order = self.pos.db.get_order_by_id(order_id)
            }
            this.renderElement();
            this.$('.back').click(function(){
                self.gui.back();
                if(params.previous){
                    self.pos.get_order().set_screen_data('previous-screen', params.previous);
                    if(params.partner_id){
                        $('.client-list-contents').find('.client-line[data-id="'+ params.partner_id +'"]').click();
                        $('#show_client_history').click();
                    }
                }

            });
            if(self.clicked_order){
				this.$('.pay').click(function(){
                    self.pos.gui.screen_instances.orderlist.pay_order_due(order_id)
                });
				var contents = this.$('.order-details-contents');
				contents.append($(QWeb.render('OrderDetails',{widget:this, order:self.clicked_order})));
				new Model('account.bank.statement.line').call('search_read',
				[[['pos_statement_id', '=', order_id]]], {}, {'async': true})
				.then(function(statements){
					if(statements){
						self.render_list(statements);
					}
				});
            }

        },
        render_list: function(statements){
            var contents = this.$el[0].querySelector('.paymentline-list-contents');
            contents.innerHTML = "";
            for(var i = 0, len = Math.min(statements.length,1000); i < len; i++){
                var statement = statements[i];
                var paymentline_html = QWeb.render('PaymentLines',{widget: this, statement:statement});
                var paymentline = document.createElement('tbody');
                paymentline.innerHTML = paymentline_html;
                paymentline = paymentline.childNodes[1];
                contents.append(paymentline);
            }

        },
	});
	gui.define_screen({name:'orderdetail', widget: OrderDetailScreenWidget});

    screens.ClientListScreenWidget.include({
        show: function(){
            var self = this;
            this._super();
            var $show_customers = $('#show_customers');
            var $show_client_history = $('#show_client_history');
            if (this.pos.get_order().get_client() || this.new_client) {
                $show_client_history.removeClass('oe_hidden');
            }
            $show_customers.off().on('click', function(e){
                $('.client-list').removeClass('oe_hidden');
                $('#customer_history').addClass('oe_hidden')
                $show_customers.addClass('oe_hidden');
                $show_client_history.removeClass('oe_hidden');
            })
        },
        toggle_save_button: function(){
            var self = this;
            this._super();
            var $show_customers = this.$('#show_customers');
            var $show_client_history = this.$('#show_client_history');
            var $customer_history = this.$('#customer_history');
            var client = this.new_client || this.pos.get_order().get_client();
            if (this.editing_client) {
                $show_customers.addClass('oe_hidden');
                $show_client_history.addClass('oe_hidden');
            } else {
                if(client){
                    $show_client_history.removeClass('oe_hidden');
                    $show_client_history.off().on('click', function(e){
                        self.render_client_history(client);
                        $('.client-list').addClass('oe_hidden');
                        $customer_history.removeClass('oe_hidden');
                        $show_client_history.addClass('oe_hidden');
                        $show_customers.removeClass('oe_hidden');
                    });
                } else {
                    $show_client_history.addClass('oe_hidden');
                    $show_client_history.off();
                }
            }
        },
        _get_customer_history: function(partner){
            new Model('pos.order').call('search_read', [[['partner_id', '=', partner.id]]], {}, {async: false})
            .then(function(orders){
                if(orders){
                     var filtered_orders = orders.filter(function(o){return (o.amount_total - o.amount_paid) > 0})
                     partner['history'] = filtered_orders
                }

            })
        },
        render_client_history: function(partner){
            var self = this;
            var contents = this.$el[0].querySelector('#client_history_contents');
            contents.innerHTML = "";
            self._get_customer_history(partner);
            if(partner.history){
                for (var i=0; i < partner.history.length; i++){
                    var history = partner.history[i];
                    var history_line_html = QWeb.render('ClientHistoryLine', {
                        partner: partner,
                        order: history,
                        widget: self,
                    });
                    var history_line = document.createElement('tbody');
                    history_line.innerHTML = history_line_html;
                    history_line = history_line.childNodes[1];
                    history_line.addEventListener('click', function(e){
                        var order_id = $(this).data('id');
                        if(order_id){
                            var previous = self.pos.get_order().get_screen_data('previous-screen');
                            self.gui.show_screen('orderdetail', {
                                order_id: order_id,
                                previous: previous,
                                partner_id: partner.id
                            });
                        }
                    })
                    contents.appendChild(history_line);
                }
            }
        },
        render_payment_history: function(){
            var self = this;
            var $client_details_box = $('.client-details-box');
            $client_details_box.addClass('oe_hidden');
        }
	});

});