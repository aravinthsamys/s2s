from django.shortcuts import render
from django.http import JsonResponse
import random
import time
from agora_token_builder import RtcTokenBuilder, RtmTokenBuilder
from .models import RoomMember
import json
from django.views.decorators.csrf import csrf_exempt
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk

# Download necessary NLTK datasets
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
nltk.download('stopwords')

from django.contrib.staticfiles import finders


# Lobby page
def lobby(request):
    return render(request, 'base/lobby.html')


# Room page
def room(request):
    return render(request, 'base/room.html')


# RTC token generation
def getToken(request):
    appId = "ce0e070ac03f4922af4259eeb5c64fd2"
    appCertificate = "10b26fc9a122472f960edd7a96a9ad84"
    channelName = request.GET.get('channel')
    uid = str(random.randint(1, 230))
    expirationTimeInSeconds = 3600
    currentTimeStamp = int(time.time())
    privilegeExpiredTs = currentTimeStamp + expirationTimeInSeconds
    role = 1

    token = RtcTokenBuilder.buildTokenWithUid(appId, appCertificate, channelName, uid, role, privilegeExpiredTs)
    return JsonResponse({'token': token, 'uid': uid}, safe=False)


# RTM token generation
def get_rtm_token(request):
    app_id = "ce0e070ac03f4922af4259eeb5c64fd2"
    app_certificate = "fd53193fa409464980a0837bca65793a"
    user_id = str(request.GET.get('uid'))

    if not user_id:
        return JsonResponse({'error': 'User ID is required'}, status=400)

    expiration_time_in_seconds = 3600
    current_timestamp = int(time.time())
    privilege_expired_ts = current_timestamp + expiration_time_in_seconds

    token = RtmTokenBuilder.buildToken(app_id, app_certificate, user_id, 1, privilege_expired_ts)
    return JsonResponse({'rtmtoken': token, 'uid': user_id}, safe=False)


@csrf_exempt
def createMember(request):
    data = json.loads(request.body)
    member, created = RoomMember.objects.get_or_create(
        name=data['name'],
        uid=data['UID'],
        room_name=data['room_name']
    )
    return JsonResponse({'name': data['name']}, safe=False)


def getMember(request):
    uid = request.GET.get('UID')
    room_name = request.GET.get('room_name')
    try:
        member = RoomMember.objects.get(uid=uid, room_name=room_name)
        return JsonResponse({'name': member.name}, safe=False)
    except RoomMember.DoesNotExist:
        return JsonResponse({'error': 'Member not found'}, status=404)


@csrf_exempt
def deleteMember(request):
    data = json.loads(request.body)
    try:
        member = RoomMember.objects.get(
            name=data['name'],
            uid=data['UID'],
            room_name=data['room_name']
        )
        member.delete()
        return JsonResponse('Member deleted', safe=False)
    except RoomMember.DoesNotExist:
        return JsonResponse({'error': 'Member not found'}, status=404)


@csrf_exempt
def animation_view(request):
    if request.method == 'POST':
        text = request.POST.get('sen', '').lower()

        words = word_tokenize(text)
        tagged = nltk.pos_tag(words)

        # Tense identification
        tense = {
            "future": len([w for w in tagged if w[1] == "MD"]),
            "present": len([w for w in tagged if w[1] in ["VBP", "VBZ", "VBG"]]),
            "past": len([w for w in tagged if w[1] in ["VBD", "VBN"]]),
            "present_continuous": len([w for w in tagged if w[1] == "VBG"]),
        }

        stop_words = set(stopwords.words('english'))
        lr = WordNetLemmatizer()
        filtered_text = []

        for w, p in zip(words, tagged):
            if w not in stop_words:
                if p[1] in ['VBG', 'VBD', 'VBZ', 'VBN', 'NN']:
                    filtered_text.append(lr.lemmatize(w, pos='v'))
                elif p[1] in ['JJ', 'JJR', 'JJS', 'RBR', 'RBS']:
                    filtered_text.append(lr.lemmatize(w, pos='a'))
                else:
                    filtered_text.append(lr.lemmatize(w))

        # Pronoun correction
        words = ['Me' if w == 'I' else w for w in filtered_text]

        probable_tense = max(tense, key=tense.get)
        if probable_tense == "past" and tense["past"] >= 1:
            words = ["Before"] + words
        elif probable_tense == "future" and tense["future"] >= 1:
            if "Will" not in words:
                words = ["Will"] + words
        elif probable_tense == "present" and tense["present_continuous"] >= 1:
            words = ["Now"] + words

        final_words = []
        for w in words:
            path = "data/" + w.title() + ".mp4"
            f = finders.find(path)
            if not f:
                final_words.extend([c.upper() for c in w])
            else:
                final_words.append(w.title())

        return JsonResponse({"text": text, "words": final_words})
    else:
        return render(request, 'base/room.html')
