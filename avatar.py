from cloudinary.uploader import upload

@app.put("/users/me/avatar")
async def update_avatar(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    upload_result = upload(file.file)

    current_user.avatar_url = upload_result["secure_url"]
    db.commit()

    return {"message": "Avatar updated successfully"}