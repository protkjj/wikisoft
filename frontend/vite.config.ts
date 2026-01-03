import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3005,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8004',
        changeOrigin: true
      }
    }
  },
  build: {
    // 청크 크기 경고 임계값 (KB)
    chunkSizeWarningLimit: 600,

    // 소스맵 생성 (프로덕션 디버깅용, 필요시 false로)
    sourcemap: false,

    // Terser 최적화
    minify: 'terser',
    terserOptions: {
      compress: {
        // 프로덕션에서 console 제거
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.debug']
      },
      format: {
        // 주석 제거
        comments: false
      }
    },

    // Rollup 옵션 (코드 스플리팅)
    rollupOptions: {
      output: {
        // 벤더 청크 분리 (캐싱 최적화)
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'ui-vendor': ['react-markdown']
        },
        // 파일명 패턴
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]'
      }
    },

    // 최적화 옵션
    cssCodeSplit: true,
    assetsInlineLimit: 4096, // 4KB 이하 파일은 base64 인라인
  },

  // 프리뷰 서버 설정
  preview: {
    port: 3005,
    strictPort: true
  }
})
