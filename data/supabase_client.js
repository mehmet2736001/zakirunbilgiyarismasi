/**
 * ZAKİRUN KUR'AN TV // SUPABASE AUTH & CLOUD SYNC MOTORU
 * =======================================================
 * Supabase Proje URL: https://npggerrhnkpqxnrwzcfj.supabase.co
 * Anon Public Key: Aktif
 */

(function() {
    const SUPABASE_CONFIG = {
        url: "https://npggerrhnkpqxnrwzcfj.supabase.co",
        anonKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5wZ2dlcnJobmtwcXhucnd6Y2ZqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgwNTY4NjcsImV4cCI6MjEwMzYzMjg2N30.khiNRufN9gR4HF6zvVxeXmQkLf4wekuikWcm8yvQw6Q"
    };

    let client = null;

    function getClient() {
        if (!client) {
            if (window.supabase && typeof window.supabase.createClient === 'function') {
                client = window.supabase.createClient(SUPABASE_CONFIG.url, SUPABASE_CONFIG.anonKey, {
                    auth: {
                        persistSession: true,
                        autoRefreshToken: true,
                        detectSessionInUrl: true
                    }
                });
            } else {
                console.warn("[Zakirun Supabase] supabase-js SDK henüz yüklenmedi.");
            }
        }
        return client;
    }

    const DEFAULT_SETTINGS = {
        reciter: 'husary_muallim',     // husary_muallim, menshawi_muallim, abdulbasit
        font: 'zakirun_uthmani',       // zakirun_uthmani, scheherazade, amiri
        fontSize: 'normal',            // normal, large, xlarge
        soundEffects: true,            // true, false
        soundVolume: 80,               // 0 - 100
        autoPlayAudio: true            // soru/hücreye odaklanınca otomatik çal
    };

    const ZakirunSupabase = {
        config: SUPABASE_CONFIG,

        getClient: getClient,

        /**
         * Google OAuth ile Giriş Başlatır
         */
        async signInWithGoogle(redirectTo) {
            const sb = getClient();
            if (!sb) throw new Error("Supabase kütüphanesi yüklenemedi.");

            const dest = redirectTo || (window.location.origin + '/giris');
            const { data, error } = await sb.auth.signInWithOAuth({
                provider: 'google',
                options: {
                    redirectTo: dest,
                    queryParams: {
                        access_type: 'offline',
                        prompt: 'consent'
                    }
                }
            });

            if (error) throw error;
            return data;
        },

        /**
         * E-Posta ve Şifre ile Yeni Kullanıcı Kaydı
         */
        async signUpWithEmail(name, email, password, hifzTier = "Mutavassıt (Orta)") {
            const sb = getClient();
            if (!sb) throw new Error("Supabase kütüphanesi yüklenemedi.");

            const avatarUrl = `https://api.dicebear.com/7.x/bottts/svg?seed=${encodeURIComponent(name)}`;

            const { data, error } = await sb.auth.signUp({
                email: email,
                password: password,
                options: {
                    data: {
                        name: name,
                        full_name: name,
                        hifz_tier: hifzTier,
                        avatar_url: avatarUrl
                    }
                }
            });

            if (error) throw error;

            if (data.session && data.user) {
                const userObj = this.formatUser(data.user, name, hifzTier, avatarUrl);
                await this.syncSessionWithServer(userObj);
                return { user: userObj, session: data.session, needsConfirmation: false };
            } else if (data.user) {
                return { user: data.user, session: null, needsConfirmation: true };
            }
            return data;
        },

        /**
         * E-Posta ve Şifre ile Giriş
         */
        async signInWithEmail(email, password) {
            const sb = getClient();
            if (!sb) throw new Error("Supabase kütüphanesi yüklenemedi.");

            const { data, error } = await sb.auth.signInWithPassword({
                email: email,
                password: password
            });

            if (error) throw error;

            if (data.user) {
                const userObj = this.formatUser(data.user);
                await this.syncSessionWithServer(userObj);
                return { user: userObj, session: data.session };
            }
            return data;
        },

        /**
         * Kullanıcı Profilini Günceller (İsim, Hıfz Seviyesi, Avatar)
         */
        async updateProfile(updates) {
            const sb = getClient();
            let current = this.getLocalUser() || {};
            const merged = { ...current, ...updates };

            // 1. Supabase Auth User Metadata Güncelle
            if (sb) {
                try {
                    await sb.auth.updateUser({
                        data: {
                            name: merged.name,
                            full_name: merged.name,
                            hifz_tier: merged.hifz_tier,
                            avatar_url: merged.avatar_url
                        }
                    });
                } catch(e) {
                    console.warn("[Zakirun Supabase] updateUser metadata uyarısı:", e);
                }
            }

            // 2. Yerel Depolamayı Güncelle
            localStorage.setItem('zakirun_user', JSON.stringify(merged));

            // 3. Backend SQLite ile Senkronize Et
            try {
                await fetch('/api/auth/update-profile', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(merged)
                });
            } catch(e) {
                console.warn("[Zakirun Supabase] Backend profil güncelleme uyarısı:", e);
            }

            return merged;
        },

        /**
         * Şifre Değiştirme
         */
        async updatePassword(newPassword) {
            const sb = getClient();
            if (!sb) throw new Error("Supabase kütüphanesi yüklenemedi.");

            const { data, error } = await sb.auth.updateUser({
                password: newPassword
            });

            if (error) throw error;
            return data;
        },

        /**
         * Oturumu Kapatır
         */
        async signOut() {
            try {
                const sb = getClient();
                if (sb) {
                    await sb.auth.signOut();
                }
            } catch(e) {
                console.warn("[Zakirun Supabase] signOut hatası:", e);
            }
            localStorage.removeItem('zakirun_user');
        },

        /**
         * Mevcut Oturumu Alır
         */
        async getSession() {
            const sb = getClient();
            if (!sb) return null;
            try {
                const { data: { session }, error } = await sb.auth.getSession();
                if (error) return null;
                return session;
            } catch(e) {
                return null;
            }
        },

        /**
         * Yerel Depodaki Kullanıcıyı Döndürür
         */
        getLocalUser() {
            try {
                const raw = localStorage.getItem('zakirun_user');
                return raw ? JSON.parse(raw) : null;
            } catch(e) {
                return null;
            }
        },

        /**
         * Uygulama Ayarlarını Alır
         */
        getSettings() {
            try {
                const raw = localStorage.getItem('zakirun_settings');
                return raw ? { ...DEFAULT_SETTINGS, ...JSON.parse(raw) } : { ...DEFAULT_SETTINGS };
            } catch(e) {
                return { ...DEFAULT_SETTINGS };
            }
        },

        /**
         * Uygulama Ayarlarını Kaydeder
         */
        async saveSettings(newSettings) {
            const current = this.getSettings();
            const merged = { ...current, ...newSettings };
            localStorage.setItem('zakirun_settings', JSON.stringify(merged));

            const user = this.getLocalUser();
            if (user && user.id) {
                try {
                    await fetch('/api/auth/update-settings', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ userId: user.id, settings: merged })
                    });
                } catch(e) {}
            }
            return merged;
        },

        /**
         * Oturum Değişikliklerini Dinler (Google dönüşü vb.)
         */
        onAuthStateChange(callback) {
            const sb = getClient();
            if (!sb) return { data: { subscription: { unsubscribe: () => {} } } };
            return sb.auth.onAuthStateChange(async (event, session) => {
                if (session && session.user) {
                    const userObj = this.formatUser(session.user);
                    await this.syncSessionWithServer(userObj);
                    callback(event, userObj, session);
                } else if (event === 'SIGNED_OUT') {
                    localStorage.removeItem('zakirun_user');
                    callback(event, null, null);
                }
            });
        },

        /**
         * Supabase user objesini Zakirun formatına dönüştürür
         */
        formatUser(sbUser, defaultName = "", defaultTier = "Mutavassıt (Orta)", defaultAvatar = "") {
            const meta = sbUser.user_metadata || {};
            const name = meta.full_name || meta.name || defaultName || (sbUser.email ? sbUser.email.split('@')[0] : "Hâfız");
            const avatar = meta.avatar_url || meta.picture || defaultAvatar || `https://api.dicebear.com/7.x/bottts/svg?seed=${encodeURIComponent(name)}`;
            const tier = meta.hifz_tier || defaultTier;
            const provider = sbUser.app_metadata?.provider || 'supabase';

            return {
                id: sbUser.id,
                name: name,
                email: sbUser.email || '',
                avatar_url: avatar,
                provider: provider,
                hifz_tier: tier,
                elo: 1350
            };
        },

        /**
         * Kullanıcı bilgilerini yerel depolama ve Python backend ile senkronize eder
         */
        async syncSessionWithServer(userObj) {
            if (!userObj) return;
            localStorage.setItem('zakirun_user', JSON.stringify(userObj));
            try {
                await fetch('/api/auth/sync-session', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(userObj)
                });
            } catch(e) {
                console.warn("[Zakirun Supabase] Backend senkronizasyon uyarısı:", e);
            }
        }
    };

    window.ZakirunSupabase = ZakirunSupabase;
})();
