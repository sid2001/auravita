from serializers.user import user_data_serializer

def user_files_serializer(data) -> dict :
    return user_data_serializer(data)

