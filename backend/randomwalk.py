import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import itertools

# 파일 경로 설정
FILE_PATH = './coindata/DOGE.json'

# 매매 수수료 설정 (왕복 0.04% * 2 = 0.08%)
TRANSACTION_FEE_RATE = 0.0008
INITIAL_BALANCE = 10000000  # 1,000만 원 시작

import os

# 현재 작업 디렉토리를 문자열 형태로 가져옵니다.
current_directory = os.getcwd()

print(current_directory)


# ----------------------------------------------------------------------
# 1. 데이터 로딩 함수 수정 (JSON 파일 읽기)
# ----------------------------------------------------------------------

def load_data_from_file(file_path):
	"""
	JSON 파일에서 일별 데이터를 읽어와 DataFrame으로 변환합니다.
	"""
	try:
		with open(file_path, 'r', encoding='utf-8') as f:
			data_list = json.load(f)

		df = pd.DataFrame(data_list)

		# 'trade_price'가 반드시 존재해야 함.
		if 'trade_price' not in df.columns:
			raise KeyError("'trade_price' 컬럼이 데이터에 없습니다.")

		df['trade_price'] = df['trade_price'].astype(float)

		# 데이터가 2일 이상 있어야 변동성 분석 및 백테스팅 가능
		if len(df) < 2:
			raise ValueError("백테스팅을 수행하기에 데이터가 너무 적습니다 (최소 2일 이상 필요).")

		# 💡 핵심 수정 부분: 데이터프레임의 행 순서를 역순으로 뒤집습니다.
		# df.iloc[::-1]은 모든 행을 처음부터 끝까지 역순으로 선택합니다.
		df_reversed = df.iloc[::-1].reset_index(drop=True)

		return df_reversed

	except FileNotFoundError:
		print(f"오류: '{file_path}' 파일을 찾을 수 없습니다. 파일을 생성했는지 확인해주세요.")
		return None
	except json.JSONDecodeError:
		print(f"오류: '{file_path}' 파일의 JSON 형식이 올바르지 않습니다.")
		return None
	except Exception as e:
		print(f"데이터 로드 중 오류 발생: {e}")
		return None


# ----------------------------------------------------------------------
# 2. 리밸런싱 백테스팅 함수 정의 (이전 코드와 동일)
# ----------------------------------------------------------------------

def backtest_rebalancing(prices, band_percentage, fee_rate, initial_balance):
	"""
	주어진 가격 경로와 리밸런싱 밴드를 사용하여 50/50 전략을 백테스팅합니다.
	(로직은 이전 코드와 동일)
	"""
	initial_coin_price = prices[0]
	initial_coin_value = initial_balance / 2
	initial_cash_value = initial_balance / 2

	coin_amount = initial_coin_value / initial_coin_price
	cash_value = initial_cash_value

	for i in range(1, len(prices)):
		current_price = prices[i]
		current_coin_value = coin_amount * current_price
		total_value = current_coin_value + cash_value
		current_coin_weight = current_coin_value / total_value

		upper_band = 0.5 + (band_percentage / 2)
		lower_band = 0.5 - (band_percentage / 2)

		if current_coin_weight > upper_band:
			# 매도 (Sell)
			target_coin_value = total_value * 0.5
			sell_amount_value = current_coin_value - target_coin_value
			net_sell_cash = sell_amount_value * (1 - fee_rate / 2)

			coin_amount -= sell_amount_value / current_price
			cash_value += net_sell_cash

		elif current_coin_weight < lower_band:
			# 매수 (Buy)
			target_coin_value = total_value * 0.5
			buy_amount_value = target_coin_value - current_coin_value
			cost_to_buy = buy_amount_value / (1 - fee_rate / 2)

			if cost_to_buy > cash_value:
				continue

			coin_amount += buy_amount_value / current_price
			cash_value -= cost_to_buy

	final_value = (coin_amount * prices[-1]) + cash_value
	return final_value


# ----------------------------------------------------------------------
# 3. 최적 진폭 탐색 및 시뮬레이션 실행
# ----------------------------------------------------------------------

# 데이터 로드
df = load_data_from_file(FILE_PATH)
if df is None:
	# 데이터 로드 실패 시 종료
	exit()

prices = df['trade_price'].values

# 비교할 밴드 폭 설정 (1%부터 10%까지 1% 단위로 테스트)
band_ranges = np.arange(0.01, 0.21, 0.01)  # [0.01, 0.02, ..., 0.10]
results = {}

print("--- 리밸런싱 진폭 최적화 시뮬레이션 시작 ---")
print(f"수수료 (왕복): {TRANSACTION_FEE_RATE * 100:.2f}% | 기간: {len(prices)}일")
print("-" * 40)

# 각 밴드 폭에 대해 백테스팅 실행
for band in band_ranges:
	band_pct = band * 100

	# Buy and Hold 전략 (벤치마크)
	if band == band_ranges[0]:  # 첫 번째 루프에서 B&H 계산
		# B&H는 딱 한 번 매수/매도 수수료를 적용하여 계산
		start_coin_amount = (INITIAL_BALANCE / 2) / prices[0]
		final_value_bh = (start_coin_amount * prices[-1]) * (1 - TRANSACTION_FEE_RATE / 2) + (INITIAL_BALANCE / 2)
		results[f"Buy & Hold"] = final_value_bh

	# 리밸런싱 백테스팅 수행
	final_value = backtest_rebalancing(prices, band, TRANSACTION_FEE_RATE, INITIAL_BALANCE)

	# 결과 저장
	results[f"±{band_pct:.0f}% Band"] = final_value

	# 중간 출력
	profit = final_value - INITIAL_BALANCE
	roi = (profit / INITIAL_BALANCE) * 100
	print(f"| ±{band_pct:.0f}% Band | 최종 자산: {final_value:,.0f}원 | 수익률: {roi:.2f}% |")

# ----------------------------------------------------------------------
# 4. 결과 분석 및 시각화
# ----------------------------------------------------------------------

results_series = pd.Series(results)
best_band = results_series.idxmax()
best_return = (results_series.max() / INITIAL_BALANCE - 1) * 100

print("-" * 40)
print(f"🏆 최적 매매 진폭 결과: {best_band}")
print(f"최대 수익률: {best_return:.2f}%")

# 시각화
plt.figure(figsize=(10, 6))
results_series.sort_values(ascending=False).plot(kind='bar', color='skyblue')
plt.title('리밸런싱 밴드 폭에 따른 최종 자산 가치 비교')
plt.ylabel('최종 포트폴리오 가치 (원)')
plt.xlabel('리밸런싱 밴드 폭')
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', linestyle='--')
plt.tight_layout()
plt.show()
