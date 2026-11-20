# Oyun Konfigürasyonu

# Ekran boyutları
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Renkler
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
BLUE = (50, 100, 255)
GREEN = (50, 200, 50)
YELLOW = (255, 255, 50)
GRAY = (150, 150, 150)

# Oyuncu
PLAYER_SIZE = 10
PLAYER_COLOR = BLUE
PLAYER_SPEED = 8

# Hedef
TARGET_SIZE = 20
TARGET_COLOR = RED
TARGET_MIN_SPEED = 2
TARGET_MAX_SPEED = 8

# AI Öğrenme Parametreleri
AI_LEARNING_RATE = 0.1
DIFFICULTY_THRESHOLD = 0.6  # Zorluk seviyesi artma eşiği (isabet yüzdesi)
ADAPTATION_SPEED = 0.05     # Adaptasyon hızı
MIN_DIFFICULTY = 0.3
MAX_DIFFICULTY = 1.0

# Oyun Metrikleri
INITIAL_SHOTS_TO_TRACK = 30  # Kaç atışın istatistiği tutulacak

# Eğitim verisi: False -> atışlar oturumlar boyunca data/training_shots.csv'de birikir,
# True -> oyun her açılışta dosyayı sıfırlar
RESET_DATASET_ON_START = False

# Force model seçimi (None veya 'logistic' / 'random_forest' / 'svm_rbf' / 'poly_logistic')
# Force model choice: choose one of 'logistic', 'random_forest', 'svm_rbf', 'poly_logistic'
# Set to 'random_forest' to prefer the Random Forest model from training metrics.
FORCE_MODEL = 'poly_logistic'
