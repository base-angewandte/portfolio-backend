from rest_framework import serializers


class CleanModelSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        instance = self.Meta.model(**attrs)
        instance.clean()
        return attrs
