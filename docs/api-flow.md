# 予約フローの詳細解析

## 概要

Airリザーブの予約フローを詳細に解析し、自動化のポイントを説明します。

## 予約フローの全体像

```
カレンダーページ → 予約リンククリック → メニュー選択 → 日時選択 → 情報入力 → 確認 → 完了
```

## 各ステップの詳細解析

### 1. カレンダーページ (https://airrsv.net/kokoroto-azukari/calendar)

#### ページ構造
```html
<div class="calendar-container">
  <table class="calendar">
    <thead>
      <tr>
        <th>日</th>
        <th>月</th>
        <th>火</th>
        <th>水</th>
        <th>木</th>
        <th>金</th>
        <th>土</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td class="day-cell">
          <a href="/reserve/2024-11-01" class="available">残3</a>
        </td>
        <!-- 他の日付セル -->
      </tr>
    </tbody>
  </table>
</div>
```

#### 予約可能枠の識別
- **予約可能**: `残○` の表示
- **満員**: `満員` の表示
- **受付終了**: `受付終了` の表示
- **非表示**: 予約不可の日付

#### 自動化のポイント
```python
# 予約可能枠の検出
available_selectors = [
    'a:has-text("残")',
    '.available',
    '[class*="available"]'
]

# 除外条件
exclude_selectors = [
    ':has-text("満員")',
    ':has-text("受付終了")',
    '.disabled',
    '.unavailable'
]
```

### 2. 予約リンククリック

#### リンクの構造
```html
<a href="/reserve/2024-11-01" class="reservation-link">
  残3
</a>
```

#### 自動化のポイント
```python
async def click_reservation_link(self, slot_info: Dict, page: Page):
    """予約リンクをクリック"""
    href = slot_info.get('href')
    
    # 相対URLの場合は絶対URLに変換
    if href.startswith('/'):
        base_url = "https://airrsv.net/kokoroto-azukari"
        href = base_url + href
    
    # 予約ページに移動
    await page.goto(href, wait_until="networkidle")
```

### 3. メニュー選択

#### メニュー構造
```html
<div class="menu-selection">
  <h3>メニューを選択してください</h3>
  <div class="menu-options">
    <label>
      <input type="radio" name="menu" value="standard">
      通常預かり (2時間)
    </label>
    <label>
      <input type="radio" name="menu" value="extended">
      延長預かり (4時間)
    </label>
  </div>
</div>
```

#### 自動化のポイント
```python
async def select_menu(self, page: Page):
    """メニューを選択"""
    # 最初の選択可能なメニューを選択
    menu_selector = 'input[name="menu"]:not([disabled])'
    await page.click(menu_selector)
    
    # 次のステップボタンをクリック
    next_button = 'button:has-text("次へ"), input[type="submit"]'
    await page.click(next_button)
```

### 4. 日時選択

#### 日時選択構造
```html
<div class="datetime-selection">
  <h3>日時を選択してください</h3>
  <div class="time-slots">
    <label>
      <input type="radio" name="datetime" value="2024-11-01-09:00">
      09:00 - 11:00
    </label>
    <label>
      <input type="radio" name="datetime" value="2024-11-01-11:00">
      11:00 - 13:00
    </label>
  </div>
</div>
```

#### 自動化のポイント
```python
async def select_datetime(self, page: Page):
    """日時を選択"""
    # 希望条件に合致する時間帯を選択
    preferred_times = self.get_preferred_times()
    
    for time_slot in preferred_times:
        selector = f'input[name="datetime"][value*="{time_slot}"]'
        element = await page.query_selector(selector)
        
        if element and await element.is_enabled():
            await element.click()
            break
```

### 5. 情報入力

#### フォーム構造
```html
<form class="booking-form">
  <div class="form-group">
    <label for="booker_name">予約者氏名</label>
    <input type="text" id="booker_name" name="booker_name" required>
  </div>
  
  <div class="form-group">
    <label for="booker_email">メールアドレス</label>
    <input type="email" id="booker_email" name="booker_email" required>
  </div>
  
  <div class="form-group">
    <label for="booker_phone">電話番号</label>
    <input type="tel" id="booker_phone" name="booker_phone" required>
  </div>
  
  <div class="form-group">
    <label for="child_name">お子様の氏名</label>
    <input type="text" id="child_name" name="child_name" required>
  </div>
  
  <div class="form-group">
    <label for="child_age">年齢</label>
    <select id="child_age" name="child_age" required>
      <option value="">選択してください</option>
      <option value="0">0歳</option>
      <option value="1">1歳</option>
      <option value="2">2歳</option>
    </select>
  </div>
</form>
```

#### 自動化のポイント
```python
async def fill_booking_form(self, page: Page):
    """予約フォームに入力"""
    form_data = {
        'booker_name': self.booker_name,
        'booker_email': self.booker_email,
        'booker_phone': self.booker_phone,
        'child_name': self.child_name,
        'child_age': self.child_age
    }
    
    for field_name, value in form_data.items():
        # テキスト入力フィールド
        text_selector = f'input[name="{field_name}"], input[id="{field_name}"]'
        text_element = await page.query_selector(text_selector)
        
        if text_element:
            await text_element.fill(value)
            continue
            
        # セレクトボックス
        select_selector = f'select[name="{field_name}"], select[id="{field_name}"]'
        select_element = await page.query_selector(select_selector)
        
        if select_element:
            await select_element.select_option(value=value)
```

### 6. 確認・予約完了

#### 確認画面構造
```html
<div class="confirmation">
  <h3>予約内容の確認</h3>
  <div class="booking-summary">
    <p>日時: 2024年11月1日 09:00-11:00</p>
    <p>予約者: 山田太郎</p>
    <p>お子様: 山田花子 (2歳)</p>
  </div>
  
  <div class="confirmation-buttons">
    <button type="button" class="back-button">戻る</button>
    <button type="submit" class="confirm-button">予約確定</button>
  </div>
</div>
```

#### 自動化のポイント
```python
async def confirm_booking(self, page: Page):
    """予約を確認・完了"""
    # 確認ボタンをクリック
    confirm_selector = 'button:has-text("予約確定"), input[type="submit"]'
    await page.click(confirm_selector)
    
    # ページの変化を待機
    await page.wait_for_load_state("networkidle")
    
    # 成功メッセージの確認
    success_indicators = [
        '予約完了',
        '予約受付',
        '予約確定',
        'success'
    ]
    
    page_content = await page.content()
    for indicator in success_indicators:
        if indicator in page_content:
            return True
    
    return False
```

## エラーハンドリング

### 1. ページ読み込みエラー

```python
async def handle_page_load_error(self, page: Page, url: str):
    """ページ読み込みエラーの処理"""
    try:
        response = await page.goto(url, wait_until="networkidle", timeout=30000)
        
        if not response or response.status != 200:
            raise PageLoadError(f"Failed to load page: {response.status}")
            
    except TimeoutError:
        raise PageLoadError("Page load timeout")
    except Exception as e:
        raise PageLoadError(f"Unexpected error: {e}")
```

### 2. 要素検索エラー

```python
async def handle_element_not_found(self, selector: str, page: Page):
    """要素が見つからない場合の処理"""
    try:
        element = await page.query_selector(selector)
        
        if not element:
            # スクリーンショットを撮影
            await self.take_screenshot("element_not_found")
            
            # 代替セレクターを試行
            alternative_selectors = self.get_alternative_selectors(selector)
            
            for alt_selector in alternative_selectors:
                element = await page.query_selector(alt_selector)
                if element:
                    return element
            
            raise ElementNotFoundError(f"Element not found: {selector}")
            
    except Exception as e:
        raise ElementSearchError(f"Element search failed: {e}")
```

### 3. フォーム入力エラー

```python
async def handle_form_input_error(self, field_name: str, value: str, page: Page):
    """フォーム入力エラーの処理"""
    try:
        # フィールドのクリア
        await page.fill(f'[name="{field_name}"]', '')
        
        # 値の入力
        await page.fill(f'[name="{field_name}"]', value)
        
        # バリデーションエラーの確認
        error_element = await page.query_selector('.error, .validation-error')
        
        if error_element:
            error_text = await error_element.inner_text()
            raise FormValidationError(f"Validation error: {error_text}")
            
    except Exception as e:
        raise FormInputError(f"Form input failed: {e}")
```

## 最適化のポイント

### 1. 待機時間の最適化

```python
# 適切な待機時間の設定
WAIT_TIMES = {
    'page_load': 30000,      # 30秒
    'element_visible': 5000, # 5秒
    'form_submit': 10000,    # 10秒
    'navigation': 3000       # 3秒
}
```

### 2. リトライ戦略

```python
async def retry_with_backoff(self, func, max_retries=3):
    """指数バックオフによるリトライ"""
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            wait_time = 2 ** attempt  # 1秒, 2秒, 4秒
            await asyncio.sleep(wait_time)
```

### 3. 並列処理の活用

```python
async def parallel_form_filling(self, page: Page, form_data: Dict):
    """フォーム入力の並列処理"""
    tasks = []
    
    for field_name, value in form_data.items():
        task = self.fill_field(page, field_name, value)
        tasks.append(task)
    
    await asyncio.gather(*tasks)
```

## デバッグとテスト

### 1. スクリーンショット機能

```python
async def take_debug_screenshot(self, page: Page, step: str):
    """デバッグ用スクリーンショット"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshots/debug_{step}_{timestamp}.png"
    
    await page.screenshot(path=filename, full_page=True)
    self.logger.info(f"Debug screenshot saved: {filename}")
```

### 2. ログ出力

```python
def log_page_state(self, page: Page, step: str):
    """ページ状態のログ出力"""
    url = page.url
    title = page.title()
    
    self.logger.info(f"Step: {step}")
    self.logger.info(f"URL: {url}")
    self.logger.info(f"Title: {title}")
```

### 3. テストモード

```python
async def test_mode_execution(self, page: Page):
    """テストモードでの実行"""
    if self.dry_run:
        self.logger.info("DRY_RUN mode: Skipping actual booking")
        
        # フォーム入力まで実行
        await self.fill_booking_form(page)
        
        # 確認画面で停止
        await self.take_screenshot("test_mode_stop")
        
        return True
```

## 今後の改善点

### 1. 動的セレクター対応

- CSSセレクターの動的生成に対応
- XPathの活用
- 要素の属性ベース検索

### 2. フォーム構造の変更対応

- フォーム構造の自動検出
- フィールドマッピングの動的生成
- バリデーションルールの自動学習

### 3. パフォーマンス最適化

- 不要な待機時間の削減
- 並列処理の拡張
- キャッシュ機能の追加
