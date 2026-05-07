import { useState } from "react";
import { Link, useLocation } from "wouter";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { SiGoogle, SiGithub } from "react-icons/si";
import { useAuth } from "../lib/auth-context";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { API_BASE } from "../lib/queryClient";

const schema = z.object({
  email: z.string().email("Invalid email"),
  password: z.string().min(1, "Password required"),
});

type FormData = z.infer<typeof schema>;

export default function LoginPage() {
  const [, navigate] = useLocation();
  const { login } = useAuth();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);

  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    try {
      await login(data.email, data.password);
      navigate("/");
    } catch (e: any) {
      toast({ title: "Login failed", description: e.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const oauthRedirect = (provider: "google" | "github") => {
    window.location.href = `${API_BASE}/api/v1/oauth/${provider}`;
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <svg viewBox="0 0 24 24" className="w-8 h-8 text-primary" fill="none" stroke="currentColor" strokeWidth="1.5">
            <polyline points="3,17 8,12 12,15 16,8 21,11" strokeLinejoin="round" strokeLinecap="round" />
            <polyline points="16,8 21,8 21,13" strokeLinejoin="round" strokeLinecap="round" />
          </svg>
          <span className="font-semibold text-lg text-foreground">StockAnalysis</span>
        </div>

        <div className="bg-card border border-border rounded-lg p-6 space-y-5">
          <div>
            <h1 className="text-base font-semibold text-foreground">Sign in</h1>
            <p className="text-xs text-muted-foreground mt-0.5">Market intelligence platform</p>
          </div>

          {/* OAuth */}
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="outline"
              type="button"
              onClick={() => oauthRedirect("google")}
              data-testid="btn-google-oauth"
              className="gap-2 text-xs"
            >
              <SiGoogle className="w-3.5 h-3.5" /> Google
            </Button>
            <Button
              variant="outline"
              type="button"
              onClick={() => oauthRedirect("github")}
              data-testid="btn-github-oauth"
              className="gap-2 text-xs"
            >
              <SiGithub className="w-3.5 h-3.5" /> GitHub
            </Button>
          </div>

          <div className="relative flex items-center gap-2">
            <div className="flex-1 border-t border-border" />
            <span className="text-xs text-muted-foreground">or</span>
            <div className="flex-1 border-t border-border" />
          </div>

          {/* Email/password */}
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-xs">Email</FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        placeholder="you@example.com"
                        autoComplete="email"
                        data-testid="input-email"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-xs">Password</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="••••••••"
                        autoComplete="current-password"
                        data-testid="input-password"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button
                type="submit"
                className="w-full"
                disabled={loading}
                data-testid="btn-login"
              >
                {loading ? "Signing in…" : "Sign in"}
              </Button>
            </form>
          </Form>

          <p className="text-xs text-center text-muted-foreground">
            No account?{" "}
            <Link href="/register" className="text-primary hover:underline" data-testid="link-register">Register</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
