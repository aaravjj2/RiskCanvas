import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SendIcon } from "lucide-react";

export default function Agent() {
  return (
    <div data-testid="agent-page" className="h-full flex flex-col">
      <h1 className="text-3xl font-bold mb-6">Agent</h1>
      
      <div className="grid grid-cols-3 gap-4 flex-1">
        <div className="col-span-2 flex flex-col">
          <Card className="flex-1 flex flex-col">
            <CardHeader>
              <CardTitle>Chat</CardTitle>
              <CardDescription>Ask the risk agent questions</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              <div data-testid="chat-messages" className="flex-1 overflow-auto mb-4">
                <div className="text-muted-foreground text-center py-8">
                  Start a conversation with the agent
                </div>
              </div>
              <div className="flex gap-2">
                <Input
                  data-testid="chat-input"
                  placeholder="Ask about your portfolio..."
                  className="flex-1"
                />
                <Button data-testid="chat-send">
                  <SendIcon className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
        
        <Card data-testid="audit-log">
          <CardHeader>
            <CardTitle>Audit Log</CardTitle>
            <CardDescription>Agent execution trace</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-muted-foreground">
              No executions yet
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
