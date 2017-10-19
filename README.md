# TenementRecognition

  **Dependencies:**
- python3
- itchat
- jieba  

 **Description:**  
   This program is to collect target chat text in wechat group by using `ichat` and `jieba`. Before run the program, you need to paste some sentences separated line by line. Those sentences are relevant or similar with what your target is. For example, in train.txt there are some sentences about "I have a room to sublet". Then run start.py and use your wecaht scan the QRcode to login wechat account. This program will run automatically and when it detects target chat text, it would create a new text file named by the group name and store the target sentence in it.   
   
   > You can use pyinstaller to pack it as .exe program. I try it works(that's why I wirte in one python file).
   
 **Setp:**  
 1. Store similar target sentences in `data/train.txt`
 2. Run `start.py`
 3. Scan QRcode to login
 4. Start to collect target information automatically
   
   
 **How it works:**  
 The priciple is that compare train data and test data cosine similarity, if the value is smaller than threshould, then ignore it, oterwise accept it(now I know this method is readlly simple...).  To do preprocessing chinese sentence, I use jieba to handle with it.
