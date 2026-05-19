import Image from "next/image";
import localInfoData from "../../public/data/local-info.json";

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

export default function Home() {
  // 데이터 분류 (행사와 혜택)
  const events: InfoItem[] = localInfoData.filter((item) => item.category === "행사");
  const benefits: InfoItem[] = localInfoData.filter((item) => item.category === "혜택");

  // 오늘 날짜 가져오기 (마지막 업데이트 표시용)
  const today = new Date();
  const formattedDate = `${today.getFullYear()}년 ${today.getMonth() + 1}월 ${today.getDate()}일`;

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50/70 via-orange-50/40 to-yellow-50/70 text-slate-800 font-sans selection:bg-orange-200">
      
      {/* 1. 상단 네비게이션 헤더 */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-white/70 border-b border-orange-100/50 px-4 sm:px-8 py-4 transition-all duration-300">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl" role="img" aria-label="home">🏠</span>
            <h1 className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-orange-600 to-amber-600 bg-clip-text text-transparent">
              우리 동네 생활 정보
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-orange-100 text-orange-800 animate-pulse">
              📍 성남시 소식
            </span>
          </div>
        </div>
      </header>

      {/* 2. 메인 히어로 배너 */}
      <section className="relative overflow-hidden px-4 py-16 sm:py-20 text-center">
        <div className="absolute inset-0 bg-[radial-gradient(#f97316_1px,transparent_1px)] [background-size:24px_24px] opacity-10"></div>
        <div className="max-w-4xl mx-auto relative z-10">
          <h2 className="text-4xl sm:text-5xl font-black tracking-tight text-slate-900 leading-tight">
            매일 아침 배달되는 <br className="sm:hidden" />
            <span className="bg-gradient-to-r from-orange-500 via-amber-500 to-yellow-500 bg-clip-text text-transparent">우리 동네 진짜 정보</span>
          </h2>
          <p className="mt-4 text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
            성남시의 최신 문화 행사, 다채로운 축제부터 놓치면 손해 보는 든든한 청년·출산 지원금 혜택까지! AI가 공공데이터에서 직접 모아 알기 쉽게 알려드릴게요.
          </p>
          <div className="mt-8 flex justify-center gap-4">
            <a
              href="#events"
              className="px-6 py-3 rounded-full bg-gradient-to-r from-orange-500 to-amber-500 text-white font-semibold shadow-lg shadow-orange-500/20 hover:shadow-orange-500/40 hover:-translate-y-0.5 transition-all duration-200"
            >
              🎉 축제/행사 보기
            </a>
            <a
              href="#benefits"
              className="px-6 py-3 rounded-full bg-white text-slate-700 font-semibold border border-slate-200 hover:border-orange-200 hover:bg-orange-50/20 hover:-translate-y-0.5 transition-all duration-200"
            >
              💰 혜택/지원금 보기
            </a>
          </div>
        </div>
      </section>

      {/* 3. 콘텐츠 영역 */}
      <main className="max-w-6xl mx-auto px-4 pb-24 space-y-16">
        
        {/* 행사/축제 섹션 */}
        <section id="events" className="scroll-mt-24">
          <div className="flex items-center gap-3 mb-8 border-b border-orange-200/50 pb-4">
            <span className="text-3xl" role="img" aria-label="party popper">🎉</span>
            <div>
              <h3 className="text-2xl font-black text-slate-900 tracking-tight">이번 달 행사 & 축제</h3>
              <p className="text-xs sm:text-sm text-slate-500 mt-1">놓치지 말아야 할 성남시의 즐거운 축제와 활동 소식</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
            {events.map((event) => (
              <article 
                key={event.id} 
                className="group flex flex-col justify-between bg-white/80 backdrop-blur-md border border-white rounded-3xl p-6 shadow-sm hover:shadow-xl hover:border-orange-200 hover:-translate-y-1.5 transition-all duration-300"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-orange-100 text-orange-800">
                      {event.category}
                    </span>
                    <span className="text-xs text-slate-400 font-medium">
                      {event.startDate === event.endDate ? event.startDate : `${event.startDate} ~ ${event.endDate}`}
                    </span>
                  </div>
                  
                  <h4 className="text-xl font-bold text-slate-900 tracking-tight group-hover:text-orange-600 transition-colors duration-200">
                    {event.title}
                  </h4>
                  
                  <p className="mt-3 text-slate-600 text-sm leading-relaxed line-clamp-4">
                    {event.summary}
                  </p>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-100 space-y-2.5">
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <span className="text-slate-400" role="img" aria-label="location">📍</span>
                    <span className="truncate">{event.location}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <span className="text-slate-400" role="img" aria-label="people">👥</span>
                    <span className="truncate">{event.target}</span>
                  </div>
                  
                  <a
                    href={"/info/" + event.id + "/"}
                    className="mt-4 flex items-center justify-center gap-1 w-full py-2.5 px-4 rounded-2xl text-xs font-bold text-white bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 transition-all duration-200 shadow-md shadow-orange-500/10"
                  >
                    자세히 보기
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                    </svg>
                  </a>
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* 지원금/혜택 섹션 */}
        <section id="benefits" className="scroll-mt-24">
          <div className="flex items-center gap-3 mb-8 border-b border-emerald-200/50 pb-4">
            <span className="text-3xl" role="img" aria-label="money bag">💰</span>
            <div>
              <h3 className="text-2xl font-black text-slate-900 tracking-tight">지원금 & 생활 혜택</h3>
              <p className="text-xs sm:text-sm text-slate-500 mt-1">우리 가족, 나에게 딱 맞는 유용한 정부·지자체 복지 정책</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
            {benefits.map((benefit) => (
              <article 
                key={benefit.id} 
                className="group flex flex-col justify-between bg-white/80 backdrop-blur-md border border-white rounded-3xl p-6 shadow-sm hover:shadow-xl hover:border-emerald-200 hover:-translate-y-1.5 transition-all duration-300"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                      {benefit.category}
                    </span>
                    <span className="text-xs text-slate-400 font-medium">
                      연중 상시
                    </span>
                  </div>
                  
                  <h4 className="text-xl font-bold text-slate-900 tracking-tight group-hover:text-emerald-600 transition-colors duration-200">
                    {benefit.title}
                  </h4>
                  
                  <p className="mt-3 text-slate-600 text-sm leading-relaxed line-clamp-4">
                    {benefit.summary}
                  </p>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-100 space-y-2.5">
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <span className="text-slate-400" role="img" aria-label="location">📍</span>
                    <span className="truncate">{benefit.location}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <span className="text-slate-400" role="img" aria-label="people">👥</span>
                    <span className="truncate">{benefit.target}</span>
                  </div>
                  
                  <a
                    href={"/info/" + benefit.id + "/"}
                    className="mt-4 flex items-center justify-center gap-1 w-full py-2.5 px-4 rounded-2xl text-xs font-bold text-white bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 transition-all duration-200 shadow-md shadow-emerald-500/10"
                  >
                    자세히 보기
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                    </svg>
                  </a>
                </div>
              </article>
            ))}
          </div>
        </section>

      </main>

      {/* 4. 하단 푸터 */}
      <footer className="bg-slate-900 text-slate-400 py-12 px-4 sm:px-8 border-t border-slate-800">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6 text-center md:text-left">
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
