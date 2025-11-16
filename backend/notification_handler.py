from notifications import (
    send_notification, format_long_entry_signal, format_short_entry_signal,
    format_exit_signal, format_setup_alert, format_trailing_stop_update,
    format_risk_warning
)

class NotificationHandler:
    """Handle all notification sending"""
    
    def __init__(self, settings):
        self.settings = settings
    
    def send_entry_notification(self, symbol, direction, setup_type, entry_price,
                               stop_loss, target, master_score, weighted_rsi):
        """Send entry signal notification"""
        if direction == 'LONG':
            message = format_long_entry_signal(
                symbol, setup_type, entry_price, stop_loss, target,
                master_score, weighted_rsi
            )
        else:
            message = format_short_entry_signal(
                symbol, setup_type, entry_price, stop_loss, target,
                master_score, weighted_rsi
            )
        send_notification(message, self.settings)
    
    def send_exit_notification(self, symbol, trade, exit_reason):
        """Send exit signal notification"""
        message = format_exit_signal(
            trade['direction'], symbol, exit_reason,
            trade['entry_price'], trade['exit_price'],
            trade['pnl'], trade['pnl_percent']
        )
        send_notification(message, self.settings)
    
    def send_setup_alert(self, symbol, direction, setup_type, master_score):
        """Send setup alert notification"""
        message = format_setup_alert(
            symbol, direction, setup_type, master_score,
            'Waiting for confirmation'
        )
        send_notification(message, self.settings)
    
    def send_trailing_stop_notification(self, symbol, direction, old_sl, 
                                       new_sl, current_price):
        """Send trailing stop update notification"""
        message = format_trailing_stop_update(
            symbol, direction, old_sl, new_sl, current_price
        )
        send_notification(message, self.settings)
    
    def send_risk_warning(self, warning_type, details):
        """Send risk warning notification"""
        message = format_risk_warning(warning_type, details)
        send_notification(message, self.settings)
