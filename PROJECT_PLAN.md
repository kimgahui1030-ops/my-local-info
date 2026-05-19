# 프로젝트: 우리 동네 생활 정보 웹사이트

## 목표
공공데이터포털(data.go.kr)에서 지역 행사/축제/지원금 정보를 자동 수집하고,
AI가 매일 블로그 글을 자동 작성하며,
Google AdSense + 쿠팡 파트너스로 수익화하는 웹사이트

## 기술 스택
- Next.js (App Router) + TypeScript + Tailwind CSS
- Gemini API (AI 글 자동 생성)
- 공공데이터포털 API (지역 정보 수집)
- GitHub Actions (매일 자동 실행)
- Cloudflare Pages (무료 호스팅)

## 페이지 구성
1. 메인 페이지: 이번 달 행사/축제 + 지원금/혜택 카드 목록
2. 상세 페이지: 각 행사/혜택 클릭 시 상세 정보
3. 블로그 목록: AI가 자동 생성한 글 목록
4. 블로그 상세: 개별 블로그 글 읽기

## 수익화
- Google AdSense: 메인 페이지, 블로그 글 페이지에 광고 배치
- 쿠팡 파트너스: 블로그 글 하단에 배너

## 자동화 (GitHub Actions)
매일 아침 7시(한국시간) 자동 실행:
1. 공공데이터 API에서 최신 정보 수집
2. Gemini AI로 블로그 글 자동 작성
3. Git 커밋 & 푸시
4. Cloudflare Pages 자동 배포

## 환경변수 (나중에 .env.local에 저장)
- GEMINI_API_KEY
- PUBLIC_DATA_API_KEY
- NEXT_PUBLIC_ADSENSE_ID
- NEXT_PUBLIC_GA_ID
