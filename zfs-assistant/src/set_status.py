    def set_status(self, message, icon_name=""):
        """Set status bar message with icon"""
        self.status_label.set_text(message)
        
        if icon_name:
            self.status_icon.set_visible(True)
            self.status_icon.set_from_icon_name(icon_name)
        else:
            self.status_icon.set_visible(False)
            
        return True  # For use with timeout functions
