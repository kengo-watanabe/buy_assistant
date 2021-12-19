from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials

from PIL import ImageDraw
from PIL import ImageFont
from PIL import Image
import numpy as np

import http.client, urllib.request, urllib.parse, urllib.error, base64
import json
from io import BytesIO
import io
import os
import streamlit as st
import requests
from googletrans import Translator

import config

translator = Translator()

def update_txtbox():
   st.session_state.object_list.append(st.session_state.txtbox1)
   

def main():
    st.title('おつかい補助アプリ')

    if "list_count" not in st.session_state:
        st.session_state.list_count = 0
        st.session_state.object_list = []
        st.session_state.exist_object_list = []
    
    if "buy_count" not in st.session_state:
        st.session_state.buy_count = 0
        
    if st.button("入力"):
        st.session_state.list_count += 1
        
    st.text_input("買いたいものを一つづつ入力して入力ボタンを押してください", key="txtbox1", on_change=update_txtbox)

    st.write("買いたいもの")
    for i in st.session_state.object_list:
        st.write(i)
        
    
    #ここから画像処理api使用
    #画像を保存するストレージを準備できなかったため、バイナリデータとして画像を処理しております
    uploaded_file = st.file_uploader("choose an image . . . ", type='jpg')
    
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        #バイナリ取得
        with io.BytesIO() as output:
            img.save(output, format="JPEG")
            binary_img = output.getvalue() 
            
        conn = http.client.HTTPSConnection('westus2.api.cognitive.microsoft.com')
        conn.request("POST", "/vision/v3.2/detect?%s" % config.params,binary_img, config.headers)
        response = conn.getresponse()
        response = json.load(response) #byte型から辞書型にする
        #apiのデータからobjectsのみを取り出す
        response = response['objects']
        
        draw = ImageDraw.Draw(img)
        
        #リストから辞書型へ取り出し
        for object in response:
            #物体の要素の取り出し
            exist_object = object.get("object")
            st.session_state.exist_object_list.append(exist_object.lower())
            #物体の位置の取り出し
            rect = object.get("rectangle")
            
            #物体を矩形で囲む
            draw.rectangle([(rect['x'], rect['y'] + rect['h']),(rect['x'] + rect['w'],rect['y'])], fill=None, outline=config.rectcolor, width=config.linewidth)
            txpos = (rect['x'], rect['y']-config.textsize-config.linewidth//2)
            txw,txh = draw.textsize(object.get("object"))
            draw.rectangle([txpos, (rect['x']+txw, rect['y'])], outline=config.rectcolor, fill=config.rectcolor, width=config.linewidth)
            draw.text((rect['x'], rect['y']-14-4//2),object.get("object"), fill=config.textcolor)
                
        st.image(img,caption='Uploaded Image.')
            
        #買い物リストと照合し、買えたものにチェックをつけて出力
        for s in st.session_state.object_list:
            if translator.translate(s, src='ja', dest='en').text.lower() in st.session_state.exist_object_list:
                print(translator.translate(s, src='ja', dest='en').text)
                st.checkbox(s, value = True)
                st.session_state.buy_count += 1
            else:
                print(translator.translate(s, src='ja', dest='en').text)
                st.checkbox(s, value = False)
                    
        if st.session_state.buy_count == len(st.session_state.object_list):
            st.write("買いたいものが買えました")
        else:
            st.write("買いたいものが買えていません")
            
if __name__ == "__main__":
    main()
