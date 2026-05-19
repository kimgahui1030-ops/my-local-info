import Link from "next/link";
import localInfoData from "../../../../public/data/local-info.json";

// TypeScript 인터페이스 정의
interface InfoItem {
  id: string;
  title: string;
  category: string;
  startDate: string;
  endDate: string;
  location: string;
  target: string;
  summary: string;
  link: string;
}

// Next.js 16+ 규격에 따른 params 타입 정의
type Params = Promise<{ id: string }>;

// 정적 내보내기(Static Export)를 위해 가능한 모든 경로(id)를 미리 알려주는 함수
export async function generateStaticParams() {
  return localInfoData.map((item) => ({
    id: item.id,
  }));
}

export default async function InfoDetailPage({ params }: { params: Params }) {
  // params가 Promise로 오기 때문에 await로 꺼내줍니다.
  const { id } = await params;

  // 일치하는 데이터 찾기
  const item = (localInfoData as InfoItem[]).find((info) => info.id === id);

  // 만약 일치하는 데이터를 찾지 못했을 때
  if (!item) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
        <span className="text-6xl mb-4">🔍</span>
        <h1 className="text-2xl font-bold text-slate-800">요청하신 정보를 찾을 수 없습니다.</h1>
        <p className="text-slate-500 mt-2">이미 존재하지 않거나 만료된 정보일 수 있습니다.</p>
        <Link 
          href="/"
          className="mt-6 px-6 py-2.5 bg-orange-500 text-white rounded-full font-semibold shadow-md shadow-orange-500/10 hover:shadow-orange-500/20 hover:-translate-y-0.5 transition-all"
        >
          메인 화면으로 돌아가기
        </Link>
      </div>
    );
  }

  // 오늘 날짜 및 년도 구하기
  const today = new Date();
  const formattedDate = `${today.getFullYear()}년 ${today.getMonth() + 1}월 ${today.getDate()}일`;

  // 카테고리 색상 세팅
  const isEvent = item.category === "행사";
  const categoryTheme = isEvent 
    ? {
        badgeBg: "bg-orange-100 text-orange-800",
        btnBg: "bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 shadow-orange-500/10 hover:shadow-orange-500/20",
        borderAccent: "border-orange-500",
        glowBg: "from-orange-500/5 to-amber-500/5",
        textHover: "hover:text-orange-500",
      }
    : {
        badgeBg: "bg-emerald-100 text-emerald-800",
        btnBg: "bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 shadow-emerald-500/10 hover:shadow-emerald-500/20",
        borderAccent: "border-emerald-500",
        glowBg: "from-emerald-500/5 to-teal-500/5",
        textHover: "hover:text-emerald-500",
      };

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50/70 via-orange-50/40 to-yellow-50/70 text-slate-800 font-sans selection:bg-orange-200 flex flex-col justify-between">
      
      {/* 1. 상단 네비게이션 헤더 */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-white/70 border-b border-orange-100/50 px-4 sm:px-8 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            <span className="text-2xl group-hover:scale-110 transition-transform" role="img" aria-label="home">🏠</span>
            <h1 className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-orange-600 to-amber-600 bg-clip-text text-transparent">
              우리 동네 생활 정보
            </h1>
          </Link>
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-orange-100 text-orange-800">
            📍 성남시 소식
          </span>
        </div>
      </header>

      {/* 2. 상세 콘텐츠 본문 */}
      <main className="max-w-4xl mx-auto px-4 py-8 sm:py-12 flex-1 w-full">
        
        {/* 뒤로 가기 버튼 */}
        <Link 
          href="/" 
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-slate-800 transition-colors mb-6 group"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          목록으로 돌아가기
        </Link>

        {/* 상세 보기 메인 카드 */}
        <article className="bg-white/80 backdrop-blur-md border border-white rounded-3xl p-6 sm:p-10 shadow-lg relative overflow-hidden">
          
          {/* 부드러운 은은한 빛 효과 */}
          <div className={`absolute top-0 right-0 w-80 h-80 bg-gradient-to-br ${categoryTheme.glowBg} rounded-full blur-3xl -mr-20 -mt-20 -z-10`}></div>
          
          {/* 카테고리 태그 및 날짜 */}
          <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
            <span className={`px-4 py-1.5 rounded-full text-sm font-bold shadow-sm ${categoryTheme.badgeBg}`}>
              {item.category}
            </span>
            <span className="text-sm font-medium text-slate-400">
              {isEvent 
                ? `📅 ${item.startDate === item.endDate ? item.startDate : `${item.startDate} ~ ${item.endDate}`}` 
                : "📅 연중 상시 제공"}
            </span>
          </div>

          {/* 제목 */}
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight border-b border-slate-100 pb-6">
            {item.title}
          </h2>

          {/* 핵심 개요 정보 표 */}
          <div className="my-8 grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
            
            {/* 정보 1. 일시 */}
            <div className="bg-white/50 border border-slate-100 p-5 rounded-2xl flex items-start gap-3">
              <span className="text-2xl mt-0.5" role="img" aria-label="calendar">📅</span>
              <div>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">진행 일시</h4>
                <p className="text-sm font-semibold text-slate-700 leading-snug">
                  {isEvent 
                    ? `${item.startDate === item.endDate ? item.startDate : `${item.startDate} ~ ${item.endDate}`}`
                    : "현재 신청 가능 (공고 참조)"}
                </p>
              </div>
            </div>

            {/* 정보 2. 장소 */}
            <div className="bg-white/50 border border-slate-100 p-5 rounded-2xl flex items-start gap-3">
              <span className="text-2xl mt-0.5" role="img" aria-label="location">📍</span>
              <div className="min-w-0">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">위치 / 신청방법</h4>
                <p className="text-sm font-semibold text-slate-700 leading-snug break-words">
                  {item.location}
                </p>
              </div>
            </div>

            {/* 정보 3. 대상 */}
            <div className="bg-white/50 border border-slate-100 p-5 rounded-2xl flex items-start gap-3">
              <span className="text-2xl mt-0.5" role="img" aria-label="people">👥</span>
              <div className="min-w-0">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">지원 대상</h4>
                <p className="text-sm font-semibold text-slate-700 leading-snug break-words">
                  {item.target}
                </p>
              </div>
            </div>

          </div>

          {/* 상세 설명 전문 */}
          <div className="space-y-6">
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-1.5">
              <span className="w-1 h-5 bg-gradient-to-b from-orange-500 to-amber-500 rounded-full inline-block"></span>
              상세 소개 및 혜택 안내
            </h3>
            <p className="text-base text-slate-600 leading-relaxed bg-white/30 p-6 rounded-2xl border border-white/50 whitespace-pre-line">
              {item.summary}
            </p>
          </div>

          {/* 추가 친절 가이드 (로컬 정보 팁) */}
          <div className="mt-8 bg-amber-50/50 border border-amber-100 rounded-2xl p-5 flex items-start gap-3">
            <span className="text-xl" role="img" aria-label="bulb">💡</span>
            <div className="text-xs sm:text-sm text-slate-600 leading-relaxed">
              <p className="font-bold text-slate-800 mb-1">수석 개발자의 꿀팁!</p>
              본 소식은 실시간으로 업데이트되는 공공기관 공식 자료를 기반으로 하고 있습니다. 인기가 많아 선착순 조기 마감되거나 일정 등이 변경될 수 있으니 꼭 하단의 **'자세히 보기'** 버튼을 눌러 공식 사이트 안내를 한 번 더 체크하시는 걸 권장해 드립니다!
            </div>
          </div>

          {/* 하단 액션 버튼들 */}
          <div className="mt-10 pt-8 border-t border-slate-100 flex flex-col sm:flex-row gap-4 justify-between items-center">
            <Link 
              href="/" 
              className="w-full sm:w-auto px-6 py-3 border border-slate-200 text-slate-600 rounded-2xl font-bold hover:bg-slate-50 transition-all text-center"
            >
              ← 목록으로 돌아가기
            </Link>
            
            <a
              href={item.link}
              className={`w-full sm:w-auto px-8 py-3 rounded-2xl text-white font-bold text-center flex items-center justify-center gap-1 shadow-md transition-all duration-200 hover:-translate-y-0.5 ${categoryTheme.btnBg}`}
            >
              공식 사이트에서 자세히 보기 →
            </a>
          </div>

        </article>
      </main>

      {/* 3. 하단 푸터 */}
      <footer className="bg-slate-900 text-slate-400 py-12 px-4 sm:px-8 border-t border-slate-800 mt-16">
        <div className="max-w-4xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6 text-center md:text-left">
          <div>
            <h4 className="text-white font-extrabold tracking-tight text-lg mb-2">🏠 우리 동네 생활 정보</h4>
            <p className="text-xs leading-relaxed max-w-md">
              본 사이트에서 제공하는 정보는 대한민국 공공데이터포털(data.go.kr)의 오픈 API를 통해 수집된 데이터에 기반하며, AI 기술을 활용해 이해하기 쉽게 다듬은 정보입니다.
            </p>
          </div>
          
          <div className="flex flex-col items-center md:items-end gap-2 text-xs">
            <div>
              <span>데이터 출처 : </span>
              <a 
                href="https://www.data.go.kr" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-orange-400 hover:underline font-semibold"
              >
                행정안전부 공공데이터포털
              </a>
            </div>
            <div>
              마지막 업데이트 : <span className="text-white font-bold">{formattedDate}</span>
            </div>
            <p className="mt-4 text-[10px] text-slate-600">
              © {today.getFullYear()} 우리 동네 생활 정보. All rights reserved.
            </p>
          </div>
        </div>
      </footer>

    </div>
  );
}
