from flask.ext import social
from flask.ext.social.datastore import ConnectionDatastore

class MongoEngineConnectionDatastore(ConnectionDatastore):
    
    def get_models(self):
        db = self.db
        
        class Connection(db.Document):
            user_id = db.StringField(max_length=255)
            provider_id = db.StringField(max_length=255)
            provider_user_id =db.StringField(max_length=255)
            access_token = db.StringField(max_length=255)
            secret = db.StringField(max_length=255)
            display_name = db.StringField(max_length=255)
            profile_url = db.StringField(max_length=512)
            image_url = db.StringField(max_length=512)
            rank = db.IntField(default=1)
        
        return Connection
    
    def _save_model(self, model):
        model.save()
        return model
    
    def _delete_model(self, *models):
        for m in models:
            m.delete()
    
    def remove_connection(self, user_id, provider_id, provider_user_id):
        self._delete_model(
            self.get_connection(user_id, provider_id, provider_user_id))
    
    def remove_all_connections(self, user_id, provider_id):
        self._delete_model(
            social.SocialConnection.objects(
                user_id=user_id, 
                provider_id=provider_id))
    
    def _get_connection_by_provider_user_id(self, provider_id, provider_user_id):
        return social.SocialConnection.objects(
            provider_id=provider_id, 
            provider_user_id=provider_user_id).first()
            
    def _get_primary_connection(self, user_id, provider_id):
        return social.SocialConnection.objects(
            user_id=user_id, 
            provider_id=provider_id).order_by('+rank').first()
        
    def _get_connection(self, user_id, provider_id, provider_user_id):
        return social.SocialConnection.objects(
            user_id=user_id, 
            provider_id=provider_id, 
            provider_user_id=provider_user_id).first()