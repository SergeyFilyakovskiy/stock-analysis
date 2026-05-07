import { Link } from "wouter";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex items-center justify-center h-full min-h-64 p-8">
      <div className="text-center space-y-3">
        <p className="text-4xl font-bold text-muted-foreground/30 font-mono">404</p>
        <p className="text-sm text-muted-foreground">Page not found</p>
        <Link href="/">
          <Button variant="outline" size="sm" className="mt-2 text-xs h-8">Go home</Button>
        </Link>
      </div>
    </div>
  );
}
