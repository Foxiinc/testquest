import face_recognition


def encode_face(frame):
    rgb = frame[:, :, ::-1]
    encodings = face_recognition.face_encodings(rgb)
    return encodings[0] if encodings else None


def compare_faces(known_encoding, frame):
    rgb = frame[:, :, ::-1]
    encodings = face_recognition.face_encodings(rgb)

    if not encodings:
        return False

    result = face_recognition.compare_faces([known_encoding], encodings[0])
    return result[0]
