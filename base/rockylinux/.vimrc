" ====================================================
" [Basic Settings]
" ====================================================
set nocompatible                " Vi 호환 모드 끄기 (Vim 기능 사용)

" Encoding
set encoding=utf-8              " 내부 인코딩
set fileencodings=ucs-bom,utf-8,euc-kr,cp949 " 파일 읽을 때 시도할 인코딩 순서

" History & Backup
set history=1000                " 명령어 히스토리 1000개 저장 (기존 50개는 너무 적음)
set nobackup                    " 백업 파일 생성 안 함
set noswapfile                  " 스왑 파일 생성 안 함 (컨테이너 환경에서 추천)

" Search
set hlsearch                    " 검색어 강조
set incsearch                   " 점진적 검색 (입력하는 도중 검색)
set ignorecase                  " 검색 시 대소문자 무시
set smartcase                   " 검색어에 대문자가 있으면 대소문자 구분 (강력 추천)

" UI / UX
set ruler                       " 우측 하단에 커서 위치 표시
set number                      " 라인 번호 표시 (set nu)
set showmatch                   " 괄호 짝 보여주기
set laststatus=2                " 상태바 항상 표시
set wildmenu                    " 명령어 자동완성 메뉴 표시
set showcmd                     " 입력 중인 명령어 표시
set scrolloff=5                 " 스크롤 시 위아래 여백 5줄 확보
set backspace=indent,eol,start  " 백스페이스가 자유롭게 동작하도록 설정
set wmnu                        " 탭 자동완성시 목록 표시

" Colors
syntax on                       " 문법 강조 켜기
filetype plugin indent on       " 파일 타입별 플러그인 및 들여쓰기 활성화
" t_Co=8 설정은 제거함 (현대 터미널은 256색 기본 지원)

" ====================================================
" [Indentation & Tabs]
" ====================================================
set autoindent                  " 자동 들여쓰기
set smartindent                 " 스마트 들여쓰기
set expandtab                   " 탭을 스페이스로 변환
set tabstop=4                   " 탭 너비 4
set shiftwidth=4                " 들여쓰기 너비 4
set softtabstop=4               " 탭키 입력 시 스페이스 4개

" Make files must use real tabs
autocmd FileType make setlocal noexpandtab

" ====================================================
" [Advanced Auto Commands]
" ====================================================
if has("autocmd")
  " 파일 열 때 마지막 커서 위치 기억
  autocmd BufReadPost *
  \ if line("'\"") > 0 && line ("'\"") <= line("$") |
  \   exe "normal! g'\"" |
  \ endif
endif

" ====================================================
" [Key Mappings]
" ====================================================
let mapleader = ","

" F-keys
nnoremap <F1> :set invnumber number?<CR>
nnoremap <F2> :set invpaste paste?<CR>
nnoremap <F3> :nohls<CR>

" Buffer Navigation
nnoremap <leader>q :bp<CR>
nnoremap <leader>w :bn<CR>

" Window Resize
nnoremap <silent> <Leader>= :exe "resize +3"<CR>
nnoremap <silent> <Leader>- :exe "resize -3"<CR>
nnoremap <silent> <Leader>] :exe "vertical resize +8"<CR>
nnoremap <silent> <Leader>[ :exe "vertical resize -8"<CR>

" ====================================================
" [Filename Support]
" ====================================================
set isfname+=$,{,},(,)          " 파일명에 특수문자 허용 범위 확대
