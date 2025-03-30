import numpy as np
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ImageProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("이미지 이진화 최적화 도구")
        self.root.geometry("1200x700")
        
        # 이미지 저장 변수
        self.image = None
        
        # 상단 프레임 - 버튼 영역
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        # 이미지 로드 버튼
        self.load_btn = tk.Button(self.top_frame, text="이미지 로딩", command=self.load_image, width=15, height=2)
        self.load_btn.pack(side=tk.LEFT, padx=10)
        
        # 처리 버튼
        self.process_btn = tk.Button(self.top_frame, text="이미지 처리", command=self.process_image, width=15, height=2, state=tk.DISABLED)
        self.process_btn.pack(side=tk.LEFT, padx=10)
        
        # 이미지 표시 영역
        self.display_frame = tk.Frame(self.root)
        self.display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 원본, Otsu, POC 이미지 영역
        self.original_frame = tk.LabelFrame(self.display_frame, text="원본 이미지", width=380, height=600)
        self.original_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.original_frame.pack_propagate(False)
        
        self.otsu_frame = tk.LabelFrame(self.display_frame, text="Otsu 이진화", width=380, height=600)
        self.otsu_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.otsu_frame.pack_propagate(False)
        
        self.poc_frame = tk.LabelFrame(self.display_frame, text="POC 최적화 이진화", width=380, height=600)
        self.poc_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.poc_frame.pack_propagate(False)
        
        # 이미지 표시 레이블
        self.original_label = tk.Label(self.original_frame)
        self.original_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.otsu_label = tk.Label(self.otsu_frame)
        self.otsu_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.poc_label = tk.Label(self.poc_frame)
        self.poc_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 상태 표시줄
        self.status_var = tk.StringVar()
        self.status_var.set("이미지를 로드하세요")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def load_image(self):
        # 파일 선택 다이얼로그
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff")]
        )
        
        if file_path:
            try:
                # 이미지 로드
                self.image = cv2.imread(file_path, 0)  # 그레이스케일로 로드
                
                if self.image is None:
                    messagebox.showerror("에러", "이미지를 로드할 수 없습니다.")
                    return
                
                # 원본 이미지 표시
                self.display_image(self.image, self.original_label)
                
                # 처리 버튼 활성화
                self.process_btn.config(state=tk.NORMAL)
                
                # 상태 업데이트
                self.status_var.set(f"이미지 로드 완료: {file_path}")
                
                # 자동으로 처리 실행
                self.process_image()
                
            except Exception as e:
                messagebox.showerror("에러", f"이미지 로드 중 오류 발생: {str(e)}")
    
    def process_image(self):
        if self.image is None:
            messagebox.showwarning("경고", "처리할 이미지가 없습니다. 먼저 이미지를 로드하세요.")
            return
        
        try:
            # 상태 업데이트
            self.status_var.set("이미지 처리 중...")
            self.root.update()
            
            # Otsu 이진화
            ret_otsu, otsu_thresh = cv2.threshold(self.image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # POC 이진화
            optimum_threshold, poc_thresh = self.poc_threshold(self.image)
            
            # 이미지 표시
            self.display_image(otsu_thresh, self.otsu_label)
            self.display_image(poc_thresh, self.poc_label)
            
            # 상태 업데이트
            self.status_var.set(f"처리 완료: Otsu 임계값={ret_otsu:.1f}, POC 임계값={optimum_threshold}")
            
        except Exception as e:
            messagebox.showerror("에러", f"이미지 처리 중 오류 발생: {str(e)}")
    
    def poc_threshold(self, image):
        # 원본 이미지의 DFT 계산
        dft = np.fft.fft2(image)
        phase1 = np.angle(dft)
        
        # 임계값 범위 설정
        rho_min = 10
        rho_max = 245
        
        # 상관관계 초기화
        corr = float('-inf')
        optimum_threshold = 0
        
        # 임계값 범위에서 최적의 임계값 찾기
        for rho in range(rho_min, rho_max, 5):  # 속도를 위해 5단위로 건너뛰기
            # 이미지 이진화
            ret, thresh = cv2.threshold(image, rho, 255, cv2.THRESH_BINARY)
            
            # 이진화된 이미지의 DFT 계산
            dft_thresh = np.fft.fft2(thresh)
            phase_th = np.angle(dft_thresh)
            
            # 정규화된 상관관계 계산 (개선된 방식)
            correlation = np.corrcoef(phase1.flatten(), phase_th.flatten())[0, 1]
            
            # NaN 값 처리
            if np.isnan(correlation):
                continue
                
            # 최대 상관관계 및 임계값 업데이트
            if correlation > corr:
                corr = correlation
                optimum_threshold = rho
        
        # 최적의 임계값으로 이미지 이진화
        ret, poc_thresh = cv2.threshold(image, optimum_threshold, 255, cv2.THRESH_BINARY)
        
        return optimum_threshold, poc_thresh
    
    def display_image(self, img, label):
        # 이미지를 PIL 형식으로 변환
        img_pil = Image.fromarray(img)
        
        # 레이블 크기에 맞게 이미지 크기 조정
        label_width = label.winfo_width()
        label_height = label.winfo_height()
        
        # 레이블 크기가 0이면 기본값 사용
        if label_width <= 1:
            label_width = 350
        if label_height <= 1:
            label_height = 550
            
        # 원본 이미지 비율 유지하면서 크기 조정
        img_width, img_height = img_pil.size
        ratio = min(label_width / img_width, label_height / img_height)
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        img_pil = img_pil.resize((new_width, new_height), Image.LANCZOS)
        
        # Tkinter 이미지로 변환
        img_tk = ImageTk.PhotoImage(img_pil)
        
        # 레이블에 이미지 표시
        label.config(image=img_tk)
        label.image = img_tk  # 참조 유지

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessorApp(root)
    root.mainloop()