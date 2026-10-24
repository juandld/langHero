import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

const publicBackendUrl = (process.env.PUBLIC_BACKEND_URL || '').trim();
const allowTunnelHosts =
	process.env.ALLOW_DEV_TUNNEL_HOSTS === '1' ||
	publicBackendUrl.includes('trycloudflare.com') ||
	publicBackendUrl.includes('cloudflared');
const proxyTarget = (process.env.VITE_PROXY_BACKEND || 'http://127.0.0.1:8100').trim();

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		...(allowTunnelHosts ? { allowedHosts: true } : undefined),
		proxy: {
			'/api': proxyTarget,
			'/stream': { target: proxyTarget, ws: true },
			'/images': proxyTarget,
			'/examples': proxyTarget,
			'/voice_notes': proxyTarget
		}
	}
});
