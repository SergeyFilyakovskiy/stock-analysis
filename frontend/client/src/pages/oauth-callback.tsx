import { useEffect } from "react";
import { useLocation } from "wouter";
import { useAuth } from "../lib/auth-context";
import { useToast } from "@/hooks/use-toast";

/**
 * After OAuth redirect the backend sends the user to:
 *   /oauth/callback?access_token=xxx&refresh_token=yyy
 *
 * This page picks up the tokens from the URL, passes them to AuthContext,
 * then navigates home.
 *
 * Note: if your backend issues a different redirect (e.g. directly sets
 * tokens in the HTML page or uses a different query param naming),
 * adjust this component accordingly.
 */
export default function OAuthCallbackPage() {
  const [, navigate] = useLocation();
  const { handleOAuthCallback } = useAuth();
  const { toast } = useToast();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const access = params.get("access_token");
    const refresh = params.get("refresh_token");

    if (access && refresh) {
      handleOAuthCallback(access, refresh)
        .then(() => navigate("/"))
        .catch((e) => {
          toast({ title: "OAuth error", description: e.message, variant: "destructive" });
          navigate("/login");
        });
    } else {
      // No tokens — something went wrong with the OAuth flow
      toast({ title: "OAuth error", description: "No tokens received", variant: "destructive" });
      navigate("/login");
    }
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-3">
        <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
        <p className="text-sm text-muted-foreground">Completing sign in…</p>
      </div>
    </div>
  );
}
