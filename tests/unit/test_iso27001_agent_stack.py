import aws_cdk as core
import aws_cdk.assertions as assertions

from iso27001_agent.iso27001_agent_stack import Iso27001AgentStack

# example tests. To run these tests, uncomment this file along with the example
# resource in iso27001_agent/iso27001_agent_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = Iso27001AgentStack(app, "iso27001-agent")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
