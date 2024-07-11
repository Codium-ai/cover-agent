using CalculatorApi.Controllers;
using Microsoft.AspNetCore.Mvc;
using Xunit;

public class CalculatorControllerTests
{
    [Fact]
    public void Add_ReturnsCorrectResult()
    {
        // Arrange
        var controller = new CalculatorController();

        // Act
        var result = controller.Add(5, 3) as OkObjectResult;

        // Assert
        Assert.NotNull(result);
        Assert.Equal(200, result.StatusCode);
        Assert.Equal(8.0, result.Value);
    }
}