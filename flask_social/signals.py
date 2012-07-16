
import blinker

signals = blinker.Namespace()

social_connection_created = signals.signal("connection-created")

social_connection_failed = signals.signal("connection-failed")

social_connection_removed = signals.signal("connection-removed")

social_login_failed = signals.signal("login-failed")

social_login_completed = signals.signal("login-success")
